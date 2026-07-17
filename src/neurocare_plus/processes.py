import time
import multiprocessing as mp
import queue
import numpy as np
from typing import Any, Optional, Dict
from datetime import datetime

import serial.tools.list_ports
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
from mne_lsl.lsl import StreamInfo, StreamOutlet

from typing import Literal
from pydantic import BaseModel


class CmdMsg(BaseModel):
    target: Literal["EEG", "EMOTIBIT"]
    action: Literal["OPEN_DEVICE", "CLOSE_DEVICE",
                    "START_STREAM", "STOP_STREAM",
                    "START_RECORD", "STOP_RECORD", 
                    "IMPEDANCE MODE", "EXIT"]
    data: Optional[Dict[str, Any]] = None   # Additional parameters (e.g., sample rate, channels)

class StatusMpMsg(BaseModel):
    source: Literal["EEG", "EMOTIBIT"]
    state: Literal["OPEN_DEVICE", "CLOSE_DEVICE",
                   "START_STREAM", "STOP_STREAM",
                   "START_RECORD", "STOP_RECORD", 
                   "IMPEDANCE MODE", "ERROR", "EXIT"]
    message: Optional[str] = None  # Error Trace
    data: Optional[Dict[str, Any]] = None   # Payload (e.g., battery level, impedance values)


def find_cyton_port():
    """Automatically discover the OpenBCI Cyton USB Dongle serial port."""
    # Standard FTDI FT230X identifiers used by OpenBCI
    CYTON_VID = 0x0403
    CYTON_PID = 0x6015

    ports = serial.tools.list_ports.comports()
    for port in ports:
        # OpenBCI dongles typically use FTDI chips (FT231X or similar)
        # Checking the description or manufacturer strings for matches
        
        # Strategy 1: Check by exact Vendor and Product ID
        if port.vid == CYTON_VID and port.pid == CYTON_PID:
            return port.device
        
        # Strategy 2: Fallback check for common string identifiers (useful across different OS)
        desc = port.description.lower()
        hwid = port.hwid.lower()
        if "ftdi" in desc or "usb" in desc or "ft231x" in hwid:
            print(f"Found potential OpenBCI Dongle: {port.device} ({port.description})")
            return port.device
            
    raise RuntimeError("Could not automatically find the OpenBCI Cyton USB Dongle")


def eeg_process(cmd_queue: mp.Queue, status_queue: mp.Queue, is_demo):
    # Process Initialization
    process_id = "EEG"
    print(f'[{process_id}] Process Starting')
    is_streaming = False
    in_impedance_mode = False

    try:
        # Brainflow Initialization
        if not is_demo: 
            BOARD_ID = BoardIds.CYTON_BOARD.value
            SAMPLING_RATE = BoardShim.get_sampling_rate(BOARD_ID)
            EEG_CHANNELS = BoardShim.get_eeg_channels(BOARD_ID)
            NUM_EEG_CH = len(EEG_CHANNELS)

        else:
            BOARD_ID = BoardIds.SYNTHETIC_BOARD.value
            SAMPLING_RATE = BoardShim.get_sampling_rate(BOARD_ID)
            EEG_CHANNELS = BoardShim.get_eeg_channels(BOARD_ID)[:8]
            NUM_EEG_CH = len(EEG_CHANNELS)
                                            
        # Initialization
        CHUNK_SIZE = 2
        POLLING_TIME = 1.0/SAMPLING_RATE  # How fast is the Process being polled

        # MNE-LSL Initialization
        LSL_STREAM_NAME = "EEG_Board"
        outlet_stream = StreamOutlet(StreamInfo(LSL_STREAM_NAME, 'EEG', 
                                                NUM_EEG_CH, SAMPLING_RATE,'float32', source_id='123'))
        
        while True:
            try:
                cmd = cmd_queue.get_nowait()
                action = cmd.get("action")

                ### Device Commands ###
                if action == "OPEN_DEVICE":
                    
                    if not is_demo:
                        detected_port = find_cyton_port()
                        params = BrainFlowInputParams()
                        params.serial_port = detected_port
                        board = BoardShim(BOARD_ID, params)
                    else:
                        board = BoardShim(BOARD_ID, BrainFlowInputParams())

                    if not board.is_prepared():
                        board.prepare_session()
                        status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())
                
                elif action == "CLOSE_DEVICE":
                    board.release_session()
                    is_streaming = False
                    in_impedance_mode = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())
                
                elif action == "START_STREAM":
                    board.start_stream()
                    is_streaming = True
                    in_impedance_mode = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())
                
                elif action == "STOP_STREAM":
                    board.stop_stream()
                    is_streaming = False
                    in_impedance_mode = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())
                
                elif action == "START_RECORD":
                    now = datetime.now()
                    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"brainflow_raw_{timestamp}.csv"
                    board.start_stream(f"file://raw/{filename}:w")  # Saving to a file
                    is_streaming = True
                    in_impedance_mode = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action,
                                               message=f"Raw data streaming at {filename}").model_dump())
                
                elif action == "STOP_RECORD":
                    board.stop_stream()
                    is_streaming = False
                    in_impedance_mode = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action,
                                               message=f"Raw data saved at {filename}").model_dump())
                    
                elif action == "IMPEDANCE_MODE":
                    is_streaming = False
                    in_impedance_mode = True
                    status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())

                elif action == "EXIT":
                    break
                    
            except queue.Empty:
                pass

            except Exception as e:
                status_queue.put(StatusMpMsg(source=process_id, state="ERROR",
                                        message=str(e)).model_dump())

            # Data Ingestion and Streaming Modes
            if is_streaming:  # Mode
                if board.get_board_data_count() >= CHUNK_SIZE:
                    data = board.get_board_data()  # Get data from Brainflow hardware. With flushing (destructive read)
                    eeg_data = np.ascontiguousarray(data[EEG_CHANNELS].T.astype(np.float32, copy=False))
                    outlet_stream.push_chunk(eeg_data)  # Pushing Chunk Size Data to LSL Network
            
            elif in_impedance_mode:   
                in_impedance_mode = False  # Trigger only impedance mode one-time

            # Throttling to keep CPU usage low
            time.sleep(POLLING_TIME) 


    except Exception as e:
        status_queue.put(StatusMpMsg(source=process_id, state="ERROR",
                                   message=str(e)).model_dump())
    
    finally:
        del outlet_stream
        if is_streaming:
            board.stop_stream()
        try:
            if board.is_prepared():
                board.release_session()
        except:
            pass
        status_queue.put(StatusMpMsg(source=process_id, state="EXIT",
                                   message="Exiting Process").model_dump())
        

def emotibit_process(cmd_queue: mp.Queue, status_queue: mp.Queue, is_demo):
    # Process Initialization
    process_id = "EMOTIBIT"
    print(f'[{process_id}] Process Starting')
    is_streaming = False

    try:
        # Brainflow Initialization
        if not is_demo: # HW Data
            BOARD_ID = BoardIds.EMOTIBIT_BOARD.value
            # ----- PPG -----#
            AUX_SAMPLING_RATE = 100  # Emotibit Firmware 100 Hz PPG
            PPG_CHANNELS = BoardShim.get_ppg_channels(BOARD_ID, BrainFlowPresets.AUXILIARY_PRESET)
            NUM_PPG_CH = len(PPG_CHANNELS)
            # ----- EDA/TEMP -----#
            ANC_SAMPLING_RATE = BoardShim.get_sampling_rate(BOARD_ID, BrainFlowPresets.ANCILLARY_PRESET)  # Emotibit Firmware 15 Hz (EDA: 15 Hz, Temp: 7.5 Hz)
            EDA_CHANNEL = BoardShim.get_eda_channels(BOARD_ID, BrainFlowPresets.ANCILLARY_PRESET)
            TEMP_CHANNEL = BoardShim.get_temperature_channels(BOARD_ID, BrainFlowPresets.ANCILLARY_PRESET)  # Only choose the Medical Grade Thermal Sensor
            ANC_CHANNELS = EDA_CHANNEL + TEMP_CHANNEL
            NUM_ANC_CH = len(ANC_CHANNELS)

        else:  # Demo Data
            BOARD_ID = BoardIds.SYNTHETIC_BOARD.value
            # ----- PPG -----#
            AUX_SAMPLING_RATE = BoardShim.get_sampling_rate(BOARD_ID)  # Could be 100 Hz
            PPG_CHANNELS = BoardShim.get_eeg_channels(BOARD_ID)[:3]
            NUM_PPG_CH = len(PPG_CHANNELS)
            # ----- EDA/TEMP -----#
            ANC_SAMPLING_RATE = BoardShim.get_sampling_rate(BOARD_ID, BrainFlowPresets.AUXILIARY_PRESET)  # Could be 15 Hz
            ANC_CHANNELS = BoardShim.get_ppg_channels(BOARD_ID, BrainFlowPresets.AUXILIARY_PRESET)  # Temporary Data Stream
            NUM_ANC_CH = len(ANC_CHANNELS)
                                            
        # Initialization
        CHUNK_SIZE = 2
        POLLING_TIME = 1.0/AUX_SAMPLING_RATE  # How fast is the Process being polled (PPG:100 Hz)

        # MNE-LSL Initialization
        # ----- PPG -----#
        LSL_STREAM_NAME_1 = "EMOTIBIT_PPG"
        info_ppg = StreamInfo(LSL_STREAM_NAME_1, "PPG", NUM_PPG_CH, AUX_SAMPLING_RATE, "float32", "emotibit_ppg")
        info_ppg.set_channel_names(["PPG_Red", "PPG_IR", "PPG_Green"])
        outlet_stream_1 = StreamOutlet(info_ppg)
        # ----- EDA/TEMP -----#
        LSL_STREAM_NAME_2 = "EMOTIBIT_ANC"
        info_anc = StreamInfo(LSL_STREAM_NAME_2, "Multi", NUM_ANC_CH, ANC_SAMPLING_RATE, "float32", "emotibit_anc")
        info_anc.set_channel_names(["EDA", "TEMP"])
        outlet_stream_2 = StreamOutlet(info_anc)
        
        while True:
            try:
                cmd = cmd_queue.get_nowait()
                action = cmd.get("action")

                ### Device Commands ###
                if action == "OPEN_DEVICE":
                    
                    if not is_demo:
                        params = BrainFlowInputParams()
                        params.ip_address = "10.2.120.65"  # IP Address is Varying
                        params.ip_port = 3133
                        board = BoardShim(BOARD_ID, params)
                    else:
                        params = BrainFlowInputParams()
                        params.mac_address = "2"
                        board = BoardShim(BOARD_ID, params)

                    if not board.is_prepared():
                        board.prepare_session()
                        status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())
                
                elif action == "CLOSE_DEVICE":
                    board.release_session()
                    is_streaming = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())
                
                elif action == "START_STREAM":
                    board.start_stream()
                    is_streaming = True
                    status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())
                
                elif action == "STOP_STREAM":
                    board.stop_stream()
                    is_streaming = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())
                
                elif action == "START_RECORD":
                    now = datetime.now()
                    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"brainflow_raw_{timestamp}.csv"
                    board.start_stream(f"file://raw/{filename}:w")  # Saving to a file
                    is_streaming = True
                    in_impedance_mode = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action,
                                               message=f"Raw data streaming at {filename}").model_dump())
                
                elif action == "STOP_RECORD":
                    board.stop_stream()
                    is_streaming = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action,
                                               message=f"Raw data saved at {filename}").model_dump())
                    
                elif action == "IMPEDANCE_MODE":
                    is_streaming = False
                    status_queue.put(StatusMpMsg(source=process_id, state=action).model_dump())

                elif action == "EXIT":
                    break
                    
            except queue.Empty:
                pass

            except Exception as e:
                status_queue.put(StatusMpMsg(source=process_id, state="ERROR",
                                        message=str(e)).model_dump())

            # Data Ingestion and Streaming Modes
            if is_streaming:  # Mode
                if not is_demo:  # HW Data
                    # ----- PPG -----#
                    if board.get_board_data_count(preset=BrainFlowPresets.AUXILIARY_PRESET) >= CHUNK_SIZE:
                        data_1 = board.get_board_data(preset=BrainFlowPresets.AUXILIARY_PRESET)  # Get data from Brainflow hardware. With flushing (destructive read)
                        ppg_data = np.ascontiguousarray(data_1[PPG_CHANNELS].T.astype(np.float32, copy=False))
                        outlet_stream_1.push_chunk(ppg_data)  # Pushing Chunk Size Data to LSL Network
                     # ----- EDA/TEMP -----#
                    if board.get_board_data_count(preset=BrainFlowPresets.ANCILLARY_PRESET) >= CHUNK_SIZE:
                        data_2 = board.get_board_data(preset=BrainFlowPresets.ANCILLARY_PRESET)  # Get data from Brainflow hardware. With flushing (destructive read)
                        anc_data = np.ascontiguousarray(data_2[ANC_CHANNELS].T.astype(np.float32, copy=False))
                        outlet_stream_2.push_chunk(anc_data)  # Pushing Chunk Size Data to LSL Network
                else:  # Demo Data
                    if board.get_board_data_count(preset=BrainFlowPresets.DEFAULT_PRESET) >= CHUNK_SIZE:
                        data_1 = board.get_board_data(preset=BrainFlowPresets.DEFAULT_PRESET)  # Get data from Brainflow hardware. With flushing (destructive read)
                        ppg_data = np.ascontiguousarray(data_1[PPG_CHANNELS].T.astype(np.float32, copy=False))
                        outlet_stream_1.push_chunk(ppg_data)  # Pushing Chunk Size Data to LSL Network
                     # ----- EDA/TEMP -----#
                    if board.get_board_data_count(preset=BrainFlowPresets.AUXILIARY_PRESET) >= CHUNK_SIZE:
                        data_2 = board.get_board_data(preset=BrainFlowPresets.AUXILIARY_PRESET)  # Get data from Brainflow hardware. With flushing (destructive read)
                        anc_data = np.ascontiguousarray(data_2[ANC_CHANNELS].T.astype(np.float32, copy=False))
                        outlet_stream_2.push_chunk(anc_data)  # Pushing Chunk Size Data to LSL Network

            # Throttling to keep CPU usage low
            time.sleep(POLLING_TIME) 


    except Exception as e:
        status_queue.put(StatusMpMsg(source=process_id, state="ERROR",
                                   message=str(e)).model_dump())
    
    finally:
        del outlet_stream_1
        del outlet_stream_2
        if is_streaming:
            board.stop_stream()
        try:
            if board.is_prepared():
                board.release_session()
        except:
            pass
        status_queue.put(StatusMpMsg(source=process_id, state="EXIT",
                                   message="Exiting Process").model_dump())

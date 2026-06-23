import time
import multiprocessing as mp
import queue
import numpy as np
from typing import Any, Optional, Dict
from datetime import datetime

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
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


def eeg_process(cmd_queue: mp.Queue, status_queue: mp.Queue):
    # Process Initialization
    process_id = "EEG"
    print(f'[{process_id}] Process Starting')
    is_streaming = False
    in_impedance_mode = False

    try: 
        # Brainflow Initialization
        board_id = BoardIds.SYNTHETIC_BOARD.value
        sampling_rate = BoardShim.get_sampling_rate(board_id)
        eeg_channels = BoardShim.get_eeg_channels(board_id)[:8]
        num_eeg_ch = len(eeg_channels)
        board = BoardShim(board_id, BrainFlowInputParams())

        CHUNK_SIZE = 2
        POLLING_TIME = 1.0/sampling_rate  # How fast is the Process being polled
        LSL_STREAM_NAME = "Synthetic_Board"

        # MNE-LSL Initialization
        outlet_stream = StreamOutlet(StreamInfo(LSL_STREAM_NAME, 'EEG', 
                                        num_eeg_ch, sampling_rate, 'float32', 'bf_synth'))
        
        while True:
            try:
                cmd = cmd_queue.get_nowait()
                action = cmd.get("action")

                if action == "OPEN_DEVICE":
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
                    eeg_data = np.ascontiguousarray(data[eeg_channels].T.astype(np.float32, copy=False))
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
        if board.is_prepared():
            board.release_session()
        status_queue.put(StatusMpMsg(source=process_id, state="EXIT",
                                   message="Exiting Process").model_dump())
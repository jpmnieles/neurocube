import time
import queue
import threading
from datetime import datetime

from typing import Any, Optional, Dict
from pydantic import BaseModel

from mne_lsl.stream import StreamLSL


class CtrlMsg(BaseModel):
    target: str
    action: str
    data: Optional[Dict[str, Any]] = None   # Additional parameters (e.g., sample rate, channels)


class StatusMsg(BaseModel):
    source: str
    state: str
    message: Optional[str] = None  # Error Trace
    data: Optional[Dict[str, Any]] = None   # Payload (e.g., battery level, impedance values)


class ModelManager:
    def __init__(self):
        self.running = False
        self.is_streaming = False  # Controlled by the control_queue
        
        # Control Queues
        self.ctrl_queues = {
            "EEG_INLET_FILTER": queue.Queue(),
            "PPG_INLET": queue.Queue(),
            "ANC_INLET": queue.Queue()
        }

        # Data Queues
        self.data_queues = {
            "PSD_IN": queue.Queue(),
            "HR_IN": queue.Queue(),
            "GSR_IN": queue.Queue()
        }

        # Display Queues
        self.display_queues = {
            "EEG_TIME": queue.Queue(maxsize=1),
            "PPG_TIME": queue.Queue(maxsize=1),
            "TEMP_TIME": queue.Queue(maxsize=1),
            "GSR_TIME": queue.Queue(maxsize=1)
        }

        # Aggregator Queue
        self.aggregator_queue = queue.Queue(maxsize=100)
        
        # Status Queue
        self.status_queue = queue.Queue()

        # Threads
        self.threads = {
            "EEG": threading.Thread(target=self.eeg_inlet_filter_worker, daemon=True),
            "PPG": threading.Thread(target=self.ppg_inlet_worker, daemon=True),
            "ANC": threading.Thread(target=self.anc_inlet_worker, daemon=True),
        }

    def start(self):
        """Spins up all background ingest and processing threads."""
        self.running = True
        
        for t_name, thread in self.threads.items():
            thread.start()

    def close(self):
        self.running = False
        for t_name, thread in self.threads.items():  # TODO: Close the Threads Gracefully
            thread.join(timeout=1.0)
        print("Backend Model gracefully shut down.")

    ### Worker Thread Implementations ###
    
    def eeg_inlet_filter_worker(self):
        # Thread Initialization
        worker_id = "EEG"
        print(f'[{worker_id}] Thread Starting')
        is_streaming = False
        is_initialized = False
        LSL_STREAM_NAME = "EEG_Board"

        try:
            # MNE-LSL Initialization
            inlet_stream = StreamLSL(bufsize=20,            # 25 secs 
                                     name=LSL_STREAM_NAME)  # Non-blocking operation
            sampling_rate = 250  # Change to 125 Hz when EEG is 16 channels
            POLLING_TIME = 1.0/(2.0*sampling_rate)
            
            while True:

                try:
                    # Check Control Queue for UI Command
                    try:
                        cmd = self.ctrl_queues['EEG_INLET_FILTER'].get_nowait()
                        action = cmd.get("action")
                        
                        if action == "START_STREAM":  # TODO: Make this a Toggle
                            is_streaming = True
                        
                        elif action == "STOP_STREAM":
                            is_streaming = False

                    except queue.Empty:
                        pass
                    except Exception as e:  # TODO: Placeholder for any exception on the functions triggered by the command
                        self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                        message=str(e)).model_dump())

                    # Connect Once to LSL Stream
                    if not is_initialized:
                        inlet_stream.connect(acquisition_delay=None, processing_flags='all')
                        inlet_stream.filter(5.0, 50.0, picks="eeg")  # 4th Order Butterworth Filter  # TODO: Command Filter 
                        inlet_stream.notch_filter(60, picks="eeg")
                        is_initialized = True

                    # Data Ingestion from LSL Stream
                    new_data = False
                    inlet_stream.acquire()
                    if inlet_stream.n_new_samples > 0:    
                        data, timestamps = inlet_stream.get_data()
                        new_data = True

                    # Passing Data from LSL Stream to Multithread Queues
                    if is_streaming:
                        if new_data:
                            try:
                                self.display_queues["EEG_TIME"].put_nowait((data, timestamps))
                            except queue.Full:
                                print("[EEG_TIME] Queue Full")
                                dropped_data, dropped_timestamp = self.display_queues["EEG_TIME"].get_nowait()
                                self.display_queues["EEG_TIME"].put_nowait((data, timestamps))
                            
                            try:
                                self.data_queues["FFT_IN"].put_nowait((data, timestamps))
                            except queue.Full:
                                dropped_data, dropped_timestamp = self.data_queues["FFT_IN"].get_nowait()
                                self.data_queues["FFT_IN"].put_nowait((data, timestamps))

                            print(f'[LSL INLET STREAM] Data In, Time: {datetime.now()}')
                            print(f'[LSL INLET STREAM] timestamps: {timestamps[-5:]}')

                    
                    # Throttling to keep CPU usage low
                    time.sleep(POLLING_TIME)           

                except Exception as e:
                    self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                    message=str(e)).model_dump())
                

        except Exception as e:
            self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                            message=str(e)).model_dump())
        
        finally:
            inlet_stream.disconnect()


    def anc_inlet_worker(self):
        # Thread Initialization
        worker_id = "ANC"
        print(f'[{worker_id}] Thread Starting')
        is_streaming = False
        is_initialized = False
        LSL_STREAM_NAME = "EMOTIBIT_ANC"

        try:
            # MNE-LSL Initialization
            inlet_stream = StreamLSL(bufsize=20,            # 20 secs 
                                     name=LSL_STREAM_NAME)  # Non-blocking operation
            sampling_rate = 15  # Emotibit Firmware 15 Hz EDA/GSR Max
            POLLING_TIME = 1.0/(2.0*sampling_rate)

            while True:

                try:
                    # Check Control Queue for UI Command
                    try:
                        cmd = self.ctrl_queues['ANC_INLET'].get_nowait()
                        action = cmd.get("action")
                        
                        if action == "START_STREAM":  # TODO: Make this a Toggle
                            is_streaming = True
                        
                        elif action == "STOP_STREAM":
                            is_streaming = False

                    except queue.Empty:
                        pass
                    except Exception as e:  # TODO: Placeholder for any exception on the functions triggered by the command
                        self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                        message=str(e)).model_dump())

                    # Connect Once to LSL Stream
                    if not is_initialized:
                        inlet_stream.connect(acquisition_delay=None, processing_flags='all')
                        # inlet_stream.filter(5.0, 50.0, picks="ppg")  # 4th Order Butterworth Filter  # TODO: Command Filter 
                        # inlet_stream.notch_filter(60, picks="ppg")
                        is_initialized = True

                    # Data Ingestion from LSL Stream
                    new_data = False
                    inlet_stream.acquire()
                    if inlet_stream.n_new_samples > 0:    
                        data, timestamps = inlet_stream.get_data()
                        new_data = True

                    # Passing Data from LSL Stream to Multithread Queues
                    if is_streaming:
                        if new_data:
                            #----- EDA/GSR -----#
                            try:
                                self.data_queues["GSR_IN"].put_nowait((data[0,:], timestamps))
                            except queue.Full:
                                print("[GSR_IN] Queue Full")
                                dropped_data, dropped_timestamp = self.data_queues["GSR_IN"].get_nowait()
                                self.data_queues["GSR_IN"].put_nowait((data[0,:], timestamps))
                            #----- Temperature -----#
                            try:
                                self.display_queues["TEMP_TIME"].put_nowait((data[1,:], timestamps))
                            except queue.Full:
                                print("[TEMP_TIME] Queue Full")
                                dropped_data, dropped_timestamp = self.display_queues["TEMP_TIME"].get_nowait()
                                self.display_queues["TEMP_TIME"].put_nowait((data[1,:], timestamps))

                            print(f'[ANC - LSL INLET STREAM] Data In, Time: {datetime.now()}')
                            print(f'[ANC - LSL INLET STREAM] timestamps: {timestamps[-5:]}')

                    
                    # Throttling to keep CPU usage low
                    time.sleep(POLLING_TIME)           

                except Exception as e:
                    self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                    message=str(e)).model_dump())
                

        except Exception as e:
            self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                            message=str(e)).model_dump())
        
        finally:
            inlet_stream.disconnect()
    
    def ppg_inlet_worker(self):
        # Thread Initialization
        worker_id = "PPG"
        print(f'[{worker_id}] Thread Starting')
        is_streaming = False
        is_initialized = False
        LSL_STREAM_NAME = "EMOTIBIT_PPG"

        try:
            # MNE-LSL Initialization
            inlet_stream = StreamLSL(bufsize=20,            # 20 secs 
                                     name=LSL_STREAM_NAME)  # Non-blocking operation
            sampling_rate = 100  # Emotibit Firmware 100 Hz PPG
            POLLING_TIME = 1.0/(2.0*sampling_rate)

            while True:

                try:
                    # Check Control Queue for UI Command
                    try:
                        cmd = self.ctrl_queues['PPG_INLET'].get_nowait()
                        action = cmd.get("action")
                        
                        if action == "START_STREAM":  # TODO: Make this a Toggle
                            is_streaming = True
                        
                        elif action == "STOP_STREAM":
                            is_streaming = False

                    except queue.Empty:
                        pass
                    except Exception as e:  # TODO: Placeholder for any exception on the functions triggered by the command
                        self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                        message=str(e)).model_dump())

                    # Connect Once to LSL Stream
                    if not is_initialized:
                        inlet_stream.connect(acquisition_delay=None, processing_flags='all')
                        # inlet_stream.filter(5.0, 50.0, picks="ppg")  # 4th Order Butterworth Filter  # TODO: Command Filter 
                        # inlet_stream.notch_filter(60, picks="ppg")
                        is_initialized = True

                    # Data Ingestion from LSL Stream
                    new_data = False
                    inlet_stream.acquire()
                    if inlet_stream.n_new_samples > 0:    
                        data, timestamps = inlet_stream.get_data()
                        new_data = True

                    # Passing Data from LSL Stream to Multithread Queues
                    if is_streaming:
                        if new_data:
                            try:
                                self.display_queues["PPG_TIME"].put_nowait((data, timestamps))
                            except queue.Full:
                                print("[PPG_TIME] Queue Full")
                                dropped_data, dropped_timestamp = self.display_queues["PPG_TIME"].get_nowait()
                                self.display_queues["PPG_TIME"].put_nowait((data, timestamps))

                            # print(f'[PPG - LSL INLET STREAM] Data In, Time: {datetime.now()}')
                            # print(f'[PPG - LSL INLET STREAM] timestamps: {timestamps[-5:]}')

                    
                    # Throttling to keep CPU usage low
                    time.sleep(POLLING_TIME)           

                except Exception as e:
                    self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                    message=str(e)).model_dump())
                

        except Exception as e:
            self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                            message=str(e)).model_dump())
        
        finally:
            inlet_stream.disconnect()
import time
import queue
import threading
from datetime import datetime

from pathlib import Path
from liesl.files.labrecorder.cli_wrapper import LabRecorderCLI

from typing import Any, Optional, Dict
from pydantic import BaseModel

from mne_lsl.lsl import StreamInlet, resolve_streams
from mne_lsl.stream import StreamLSL

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="subprocess")


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

        # Directory
        self.base_dir = Path(__file__).resolve().parents[2]

        # Model Controllers
        self.recorder = LabRecorderController(
            data_root=self.base_dir/"data",
            executable_path=self.base_dir/"bin"/"LabRecorder-1.17.0-noble_amd64"/"bin"/"LabRecorderCLI",
            stream_args=[{"name": "EEG_Board"}, {"name": "EMOTIBIT_PPG"},
                         {"name": "EMOTIBIT_ANC"}, {"name": "PsychoPy_Markers"}]
        )
        
        # Control Queues
        self.ctrl_queues = {
            "EEG_INLET_FILTER": queue.Queue(),
            "PPG_INLET": queue.Queue(),
            "ANC_INLET": queue.Queue(),
            "MARKER_INLET": queue.Queue(),
            "RECORDER": queue.Queue()
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
            "GSR_TIME": queue.Queue(maxsize=1),
            "MARKER_TIME": queue.Queue()
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
            "MARKER": threading.Thread(target=self.marker_inlet_worker, daemon=True),
            "RECORDER": threading.Thread(target=self.recorder_worker, daemon=True)
        }

    def start(self):
        """Spins up all background ingest and processing threads."""
        self.running = True
        
        for t_name, thread in self.threads.items():
            thread.start()

    def close(self):
        self.running = False

        # Unblock the recorder thread if it's waiting on a queue command
        self.ctrl_queues["RECORDER"].put(CtrlMsg(target="RECORDER", action="SHUTDOWN").model_dump())

        for t_name, thread in self.threads.items():  # TODO: Close the Threads Gracefully
            thread.join(timeout=1.0)
        print("Backend Model gracefully shut down.")

    @staticmethod
    def _put_latest(target_queue, item):
        try:
            target_queue.put_nowait(item)
        except queue.Full:
            try:
                target_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                target_queue.put_nowait(item)
            except queue.Full:
                pass

    ### Worker Thread Implementations ###
    
    def eeg_inlet_filter_worker(self):
        # Thread Initialization
        worker_id = "EEG"
        print(f'[{worker_id}] Thread Starting')
        is_streaming = False
        is_initialized = False
        last_error = None
        LSL_STREAM_NAME = "EEG_Board"
        inlet_stream = None

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
                                                        message=f"{type(e).__name__}: {e!r}").model_dump())

                    # Connect Once to LSL Stream
                    if not is_initialized:
                        try:
                            inlet_stream.connect(acquisition_delay=None, processing_flags='all')
                            inlet_stream.filter(5.0, 50.0, picks="eeg")  # 4th Order Butterworth Filter  # TODO: Command Filter
                            inlet_stream.notch_filter(60, picks="eeg")
                            is_initialized = True
                        except Exception:
                            time.sleep(POLLING_TIME)
                            continue

                    # Data Ingestion from LSL Stream
                    new_data = False
                    inlet_stream.acquire()
                    if inlet_stream.n_new_samples > 0:    
                        data, timestamps = inlet_stream.get_data()
                        new_data = True

                    # Passing Data from LSL Stream to Multithread Queues
                    if is_streaming:
                        if new_data:
                            self._put_latest(
                                self.display_queues["EEG_TIME"], (data, timestamps)
                            )
                    
                    last_error = None
                    # Throttling to keep CPU usage low
                    time.sleep(POLLING_TIME)           

                except Exception as e:
                    message = str(e)
                    if message != last_error:
                        self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                        message=message).model_dump())
                        last_error = message
                    time.sleep(POLLING_TIME)
                

        except Exception as e:
            self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                            message=f"{type(e).__name__}: {e!r}").model_dump())
        
        finally:
            if inlet_stream is not None:
                inlet_stream.disconnect()

    def anc_inlet_worker(self):
        # Thread Initialization
        worker_id = "ANC"
        print(f'[{worker_id}] Thread Starting')
        is_streaming = False
        is_initialized = False
        last_error = None
        LSL_STREAM_NAME = "EMOTIBIT_ANC"
        inlet_stream = None

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
                                                        message=f"{type(e).__name__}: {e!r}").model_dump())

                    # Connect Once to LSL Stream
                    if not is_initialized:
                        try:
                            inlet_stream.connect(acquisition_delay=None, processing_flags='all')
                            # inlet_stream.filter(5.0, 50.0, picks="ppg")  # 4th Order Butterworth Filter
                            # inlet_stream.notch_filter(60, picks="ppg")
                            is_initialized = True
                        except Exception:
                            time.sleep(POLLING_TIME)
                            continue

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
                            self._put_latest(
                                self.display_queues["GSR_TIME"], (data[0,:], timestamps)
                            )
                            #----- Temperature -----#
                            self._put_latest(
                                self.display_queues["TEMP_TIME"], (data[1,:], timestamps)
                            )
                    
                    last_error = None
                    # Throttling to keep CPU usage low
                    time.sleep(POLLING_TIME)           

                except Exception as e:
                    message = str(e)
                    if message != last_error:
                        self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                        message=message).model_dump())
                        last_error = message
                    time.sleep(POLLING_TIME)
                

        except Exception as e:
            self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                            message=f"{type(e).__name__}: {e!r}").model_dump())
        
        finally:
            if inlet_stream is not None:
                inlet_stream.disconnect()
    
    def ppg_inlet_worker(self):
        # Thread Initialization
        worker_id = "PPG"
        print(f'[{worker_id}] Thread Starting')
        is_streaming = False
        is_initialized = False
        last_error = None
        LSL_STREAM_NAME = "EMOTIBIT_PPG"
        inlet_stream = None

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
                                                        message=f"{type(e).__name__}: {e!r}").model_dump())

                    # Connect Once to LSL Stream
                    if not is_initialized:
                        try:
                            inlet_stream.connect(acquisition_delay=None, processing_flags='all')
                            inlet_stream.filter(0.5, 8.0) # TODO: Command Filter
                            is_initialized = True
                        except Exception:
                            time.sleep(POLLING_TIME)
                            continue

                    # Data Ingestion from LSL Stream
                    new_data = False
                    inlet_stream.acquire()
                    if inlet_stream.n_new_samples > 0:    
                        data, timestamps = inlet_stream.get_data()
                        new_data = True

                    # Passing Data from LSL Stream to Multithread Queues
                    if is_streaming:
                        if new_data:
                            self._put_latest(
                                self.display_queues["PPG_TIME"], (data, timestamps)
                            )

                            # print(f'[PPG - LSL INLET STREAM] Data In, Time: {datetime.now()}')
                            # print(f'[PPG - LSL INLET STREAM] timestamps: {timestamps[-5:]}')

                    
                    last_error = None
                    # Throttling to keep CPU usage low
                    time.sleep(POLLING_TIME)           

                except Exception as e:
                    message = str(e)
                    if message != last_error:
                        self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                        message=message).model_dump())
                        last_error = message
                    time.sleep(POLLING_TIME)
                

        except Exception as e:
            self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                            message=f"{type(e).__name__}: {e!r}").model_dump())
        
        finally:
            if inlet_stream is not None:
                inlet_stream.disconnect()

    def marker_inlet_worker(self):
        worker_id = "MARKER"
        print(f'[{worker_id}] Thread Starting')
        is_streaming = True
        sampling_rate = 100  # Match the PPG polling cadence
        POLLING_TIME = 1.0/(2.0*sampling_rate)
        inlet_stream = None
        last_error = None

        while True:
            try:
                try:
                    cmd = self.ctrl_queues["MARKER_INLET"].get_nowait()
                    action = cmd.get("action")
                    if action == "START_STREAM":
                        is_streaming = True
                    elif action == "STOP_STREAM":
                        is_streaming = False
                except queue.Empty:
                    pass

                if not is_streaming:
                    time.sleep(POLLING_TIME)
                    continue

                if inlet_stream is None:
                    streams = resolve_streams(timeout=0.5)
                    marker_info = next(
                        (stream for stream in streams if stream.name == "PsychoPy_Markers"),
                        None,
                    )
                    if marker_info is None:
                        time.sleep(POLLING_TIME)
                        continue
                    inlet_stream = StreamInlet(marker_info)
                    inlet_stream.open_stream()

                chunk, timestamps = inlet_stream.pull_chunk(timeout=0.0)
                if len(chunk) > 0:
                    marker_values = [
                        str(value[0] if hasattr(value, "__len__") and not isinstance(value, str)
                            else value)
                        for value in chunk]
                    self.display_queues["MARKER_TIME"].put_nowait(
                        (marker_values, timestamps)
                    )
                last_error = None
                time.sleep(POLLING_TIME)

            except Exception as e:
                message = str(e)
                if message != last_error:
                    self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                    message=message).model_dump())
                    last_error = message
                if inlet_stream is not None:
                    try:
                        inlet_stream.close_stream()
                    except Exception:
                        pass
                    inlet_stream = None
                time.sleep(POLLING_TIME)

    def recorder_worker(self):
        worker_id = "RECORDER"
        print(f'[{worker_id}] Thread Starting')

        while self.running:
            try:
                # Blocks until a command arrives; 0.005s timeout permits checking self.running
                cmd = self.ctrl_queues["RECORDER"].get(timeout=0.005)
                data = cmd.get("data")
                action = cmd.get("action")
            except queue.Empty:
                continue

            if action == "SHUTDOWN":
                break
                
            try:
                if action == "START":
                    # LSL resolution happens in this thread, off the GUI thread
                    self.recorder.start_recording(**data)
                    self.status_queue.put(StatusMsg(source=worker_id, state="START_RECORD",
                                                    message="Recording Streams").model_dump())

                elif action == "STOP":
                    self.recorder.stop_recording()
                    self.status_queue.put(StatusMsg(source=worker_id, state="STOP_RECORD",
                                                    message=f"Data Saved at {self.recorder.target_path}").model_dump())
                    
            except Exception as e:
                self.status_queue.put(StatusMsg(source=worker_id, state="ERROR",
                                                message=f"{type(e).__name__}: {e!r}").model_dump())
            
            finally:
                self.ctrl_queues["RECORDER"].task_done()
                
        print(f'[{worker_id}] Thread Exited')


class LabRecorderController:
    def __init__(self, data_root: Path, executable_path: Path, stream_args: list):
        self.data_root = Path(data_root)
        self.lr = LabRecorderCLI(path_to_cmd=str(executable_path))
        self.stream_args = stream_args
        self.target_path = None

    def set_stream_args(self, stream_args: list):
        self.stream_args = stream_args

    def start_recording(self, subject: str, session: str, task: str, run: int):
        """Starts recording and saves inside a subject-specific folder."""
        # 1. Create a dedicated folder for the subject (e.g., data/sub-01/)
        subject_dir = self.data_root / f"sub-{subject}"
        subject_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Generate the datetime string (Format: YYYYMMDD_HHMMSS)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 3. Construct the detailed filename
        filename = f"sub-{subject}_ses-{session}_task-{task}_run-{run}_raw_{timestamp}.xdf"
        self.target_path = subject_dir / filename
        
        # 4. Start recording to the specified path
        self.lr.start_recording(filename=str(self.target_path), streamargs=self.stream_args)

    def stop_recording(self):
        """Stops the LabRecorder CLI."""
        self.lr.stop_recording()


if __name__ == '__main__':
    # Directory
    base_dir = Path(__file__).resolve().parents[2]
    
    recorder = LabRecorderController(
        data_root= base_dir/"data",
        executable_path=base_dir/"bin"/"LabRecorder-1.17.0-noble_amd64"/"bin"/"LabRecorderCLI",
        stream_args=[{"name": "EEG_Board"}, {"name": "EMOTIBIT_PPG"}, {"name": "EMOTIBIT_ANC"}]
    )
    try:
        recorder.start_recording(
            subject="S001",
            session="DAY1",
            task="ERP",
            run="001")
    except Exception as e:
        # If the wrapper throws an error or our manual check fails, raise a clean exception
        print(f"LabRecorder Error: {str(e)}")
    time.sleep(5)
    try:
        recorder.stop_recording()
    except Exception as e:
        # If the wrapper throws an error or our manual check fails, raise a clean exception
        print(f"LabRecorder Error: {str(e)}")
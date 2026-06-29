import queue
from datetime import datetime
import dearpygui.dearpygui as dpg
from mne_lsl.lsl import local_clock

from models import ModelManager
from models import CtrlMsg
from views import MainView
from processes import CmdMsg


class UiPresenter:
    def __init__(self, model: ModelManager, view: MainView,
                 cmd_mp_queues: dict, status_mp_queue, 
                 ctrl_queues:dict, display_queues: dict):
        # MVP Components
        self.model = model
        self.view = view

        # Queues
        self.cmd_mp_queues = cmd_mp_queues
        self.status_mp_queue = status_mp_queue
        self.ctrl_queues = ctrl_queues
        self.display_queues = display_queues

        # Status Flags
        self.is_eeg_connected = False

    def setup_callbacks(self):
        """Setup Model Callbacks"""
        dpg.set_item_callback("start_stream_btn", self.btn_start_eeg_cb)
        dpg.set_item_callback("stop_stream_btn", self.btn_stop_eeg_cb)
        dpg.set_item_callback("btn_eeg_device_connect", self.btn_eeg_open_device_cb)

    def setup(self):
        # Start the Model Threads
        self.model.start()

        # Initialize the View
        self.view.build()
        self.view.setup()

        # Initialize the Item Callbacks
        self.setup_callbacks()

    def run(self):
        """The main DPG rendering loop."""
        # DPG Explicit Loop
        while dpg.is_dearpygui_running():

            # Thread Functions
            self.process_status_mp_queue()
            self.process_eeg_time_series_widget()
            
            dpg.render_dearpygui_frame()  # Throttling based on the Monitor Refresh Rate

    def process_eeg_time_series_widget(self):
        while True:
            new_data = False
            try:
                data, timestamps = self.display_queues['EEG_TIME'].get_nowait()
                new_data = True
                print(f'[GUI Display] Data In, Time: {datetime.now()}')
                print(f'[GUI Display] timestamps: {timestamps[-5:]}')
            except queue.Empty:
                break

            if new_data:
                # TODO: Add Checkbox Data for enable/disable
                # TODO: Add get value option for Window Size
                WINDOW_TIME = 5  # 5 Seconds

                # Relative Timestamps
                window_start_time = local_clock()  # Latest time
                rel_timestamps =  timestamps - window_start_time

                print(f'[GUI Display] RELATIVE TIMESTAMP {rel_timestamps[-1]}')
                
                # Display for 8 Channels
                for channel_num in range(1,9):
                    dpg.set_value(f"eeg_ch{channel_num}_series", [rel_timestamps.tolist(), data.tolist()[channel_num-1]])  # For this example [0] means plotting one channel only
                    dpg.fit_axis_data(f"eeg_ch{channel_num}_y_axis")
                    dpg.set_axis_limits(f"eeg_ch{channel_num}_x_axis", -WINDOW_TIME  , 0)
                
                dpg.set_axis_limits("global_x_axis", -WINDOW_TIME, 0)

    def process_status_mp_queue(self):
        # Process all pending status messages before rendering the frame
        while True:
            try:
                status_msg = self.status_mp_queue.get_nowait()
                log_entry = f"[{status_msg['source']}] {status_msg['state']}: {status_msg['message']}\n"
            
                current_items = dpg.get_value("log_stream")
                dpg.set_value("log_stream", current_items+log_entry)
                
                # Set the scroll position to the maximum (bottom)
                dpg.set_y_scroll("status_window", 999999)

                ### Status Messages ###
                if status_msg['source'] == "EEG":

                    # Classifying Messages
                    if status_msg['state'] == "START_STREAM":
                        self.is_eeg_connected = True
                    elif status_msg['state'] == "CLOSE_DEVICE":
                        self.is_eeg_connected = False

                    if self.is_eeg_connected:
                        dpg.set_value("btn_eeg_device_connect"+"_status", "Connected")
                        dpg.configure_item("btn_eeg_device_connect"+"_indicator",color=[0, 255, 0, 255], fill=[0, 255, 0, 255])
                        dpg.configure_item("btn_eeg_device_connect", label="Stop Device")
                    else:
                        dpg.set_value("btn_eeg_device_connect"+"_status", "Disconnected")
                        dpg.configure_item("btn_eeg_device_connect"+"_indicator", color=[128, 128, 128, 255], fill=[128, 128, 128, 255])
                        dpg.configure_item("btn_eeg_device_connect", label="Start Device")  

            except queue.Empty:
                break  # No more multiprocessing status messages

    ### Callbacks ###
    
    def btn_start_eeg_cb(self):
        self.ctrl_queues['EEG_INLET_FILTER'].put(CtrlMsg(target="EEG", action="START_STREAM").model_dump())

    def btn_stop_eeg_cb(self):
        self.ctrl_queues['EEG_INLET_FILTER'].put(CtrlMsg(target="EEG", action="STOP_STREAM").model_dump())
    
    def btn_eeg_open_device_cb(self):
        if 'EEG' in self.cmd_mp_queues:
            if not self.is_eeg_connected:
                self.cmd_mp_queues['EEG'].put(CmdMsg(target="EEG", action="OPEN_DEVICE").model_dump())
                self.cmd_mp_queues['EEG'].put(CmdMsg(target="EEG", action="START_STREAM").model_dump())
            else:
                self.cmd_mp_queues['EEG'].put(CmdMsg(target='EEG', action='STOP_STREAM').model_dump())
                self.cmd_mp_queues['EEG'].put(CmdMsg(target='EEG', action='CLOSE_DEVICE').model_dump())

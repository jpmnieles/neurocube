import queue
from datetime import datetime
import dearpygui.dearpygui as dpg
from mne_lsl.lsl import local_clock

from models import ModelManager
from models import CtrlMsg
from views import MainView
from processes import CmdMsg

from widgets import EEGPlot, PPGPlot


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
        self.is_emotibit_connected = False

    def setup_callbacks(self):
        """Setup Model Callbacks"""
        dpg.set_item_callback("start_stream_btn", self.btn_start_stream_cb)
        dpg.set_item_callback("stop_stream_btn", self.btn_stop_stream_cb)
        dpg.set_item_callback("btn_eeg_device_connect", self.btn_eeg_open_device_cb)
        dpg.set_item_callback("btn_emotibit_device_connect", self.btn_emotibit_open_device_cb)

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

            # Dynamic Sizing
            self.update_window_layouts()

            # Thread Functions
            self.process_status_mp_queue()
            self.process_eeg_time_series_widget()
            self.process_ppg_time_series_widget()
            self.process_temp_time_series_widget()
            
            dpg.render_dearpygui_frame()  # Throttling based on the Monitor Refresh Rate

    def process_temp_time_series_widget(self):
        while True:
            new_data = False
            try:
                data, timestamps = self.display_queues['TEMP_TIME'].get_nowait()
                new_data = True
                print(f'[GUI TEMP Display] Data In, Time: {datetime.now()}')
                print(f'[GUI TEMP Display] timestamps: {timestamps[-5:]}')
            except queue.Empty:
                break

            if new_data:
                # Relative Timestamps
                window_start_time = local_clock()  # Latest time
                rel_timestamps =  timestamps - window_start_time
                rel_timestamps_list = rel_timestamps.tolist()

                vert_scale = dpg.get_value("combo_temp_vert_scale")

                is_auto = True

                if is_auto:
                    window_time_str = dpg.get_value("combo_temp_time_window")
                    WINDOW_TIME = PPGPlot.combo2twindow_dict[window_time_str]
                    time_mask = rel_timestamps > -WINDOW_TIME

                print(f'[GUI PPG Display] RELATIVE TIMESTAMP {rel_timestamps[-1]}')


                # Process only channel which are enabled
                channel_num = 1
                dpg.set_value(f"temp_ch{channel_num}_series", [rel_timestamps_list, data.tolist()])

                if is_auto:
                    data_filtered = data[time_mask]
                    max_data_filtered = data_filtered.max()
                    min_data_filtered = data_filtered.min()
                    dpg.set_value("Temp_widget_data_text", f"{data_filtered.mean():2.2f}°C")
                    dpg.set_axis_limits(f"temp_ch{channel_num}_x_axis", -WINDOW_TIME  , 0)
                    dpg.set_axis_limits(f"temp_ch{channel_num}_y_axis", 
                        min_data_filtered, max_data_filtered)
                    dpg.configure_item(f"temp_ch{channel_num}_max_y_axis", label=f"{max_data_filtered:.2f}")
                    dpg.configure_item(f"temp_ch{channel_num}_min_y_axis", label=f"{min_data_filtered:.2f}")

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
                # Relative Timestamps
                window_start_time = local_clock()  # Latest time
                rel_timestamps =  timestamps - window_start_time
                rel_timestamps_list = rel_timestamps.tolist()

                vert_scale = dpg.get_value("combo_vert_scale")
                is_auto = (vert_scale == 'Auto')

                if is_auto:
                    window_time_str = dpg.get_value("combo_time_window")
                    WINDOW_TIME = EEGPlot.combo2twindow_dict[window_time_str]
                    time_mask = rel_timestamps > -WINDOW_TIME

                print(f'[GUI Display] RELATIVE TIMESTAMP {rel_timestamps[-1]}')
                
                # Process only channel which are enabled
                for channel_num in range(1,9):
                    if dpg.get_value(f"en_eeg_ch{channel_num}"):
                        dpg.set_value(f"eeg_ch{channel_num}_series", [rel_timestamps_list, data[channel_num-1].tolist()])

                        if is_auto:
                            data_filtered = data[channel_num - 1][time_mask]
                            max_data_filtered = data_filtered.max()
                            min_data_filtered = data_filtered.min()
                            dpg.set_axis_limits(f"eeg_ch{channel_num}_y_axis", 
                                min_data_filtered, max_data_filtered)
                            dpg.configure_item(f"eeg_ch{channel_num}_max_y_axis", label=f"{max_data_filtered:.2f}")
                            dpg.configure_item(f"eeg_ch{channel_num}_min_y_axis", label=f"{min_data_filtered:.2f}")
                            
    def process_ppg_time_series_widget(self):
        while True:
            new_data = False
            try:
                data, timestamps = self.display_queues['PPG_TIME'].get_nowait()
                new_data = True
                # print(f'[GUI PPG Display] Data In, Time: {datetime.now()}')
                # print(f'[GUI PPG Display] timestamps: {timestamps[-5:]}')
            except queue.Empty:
                break

            if new_data:
                # Relative Timestamps
                window_start_time = local_clock()  # TODO: Pass as parameter for same time
                rel_timestamps =  timestamps - window_start_time
                rel_timestamps_list = rel_timestamps.tolist()

                vert_scale = dpg.get_value("combo_ppg_vert_scale")  # Should be ppg
                is_auto = (vert_scale == 'Auto')

                if is_auto:
                    window_time_str = dpg.get_value("combo_ppg_time_window")  # Should be ppg
                    WINDOW_TIME = PPGPlot.combo2twindow_dict[window_time_str]
                    time_mask = rel_timestamps > -WINDOW_TIME

                # print(f'[GUI PPG Display] RELATIVE TIMESTAMP {rel_timestamps[-1]}')


                # Process only channel which are enabled
                # print("[GUI PPG Display] Data Shape:", data.shape)
                for channel_num in range(1,4):
                    dpg.set_value(f"ppg_ch{channel_num}_series", [rel_timestamps_list, data[channel_num-1].tolist()])

                    if is_auto:
                        data_filtered = data[channel_num - 1][time_mask]
                        max_data_filtered = data_filtered.max()
                        min_data_filtered = data_filtered.min()
                        dpg.set_axis_limits(f"ppg_ch{channel_num}_y_axis", 
                            min_data_filtered, max_data_filtered)
                        dpg.configure_item(f"ppg_ch{channel_num}_max_y_axis", label=f"{max_data_filtered:.2f}")
                        dpg.configure_item(f"ppg_ch{channel_num}_min_y_axis", label=f"{min_data_filtered:.2f}")
                        

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
                
                ### Status Messages ###
                if status_msg['source'] == "EMOTIBIT":

                    # Classifying Messages
                    if status_msg['state'] == "START_STREAM":
                        self.is_emotibit_connected = True
                    elif status_msg['state'] == "CLOSE_DEVICE":
                        self.is_emotibit_connected = False

                    if self.is_emotibit_connected:
                        dpg.set_value("btn_emotibit_device_connect"+"_status", "Connected")
                        dpg.configure_item("btn_emotibit_device_connect"+"_indicator",color=[0, 255, 0, 255], fill=[0, 255, 0, 255])
                        dpg.configure_item("btn_emotibit_device_connect", label="Stop Device")
                    else:
                        dpg.set_value("btn_emotibit_device_connect"+"_status", "Disconnected")
                        dpg.configure_item("btn_emotibit_device_connect"+"_indicator", color=[128, 128, 128, 255], fill=[128, 128, 128, 255])
                        dpg.configure_item("btn_emotibit_device_connect", label="Start Device")

            except queue.Empty:
                break  # No more multiprocessing status messages

    ### Callbacks ###
    
    def btn_start_stream_cb(self):
        print("[GUI] Clicked Start Stream")
        self.ctrl_queues['EEG_INLET_FILTER'].put(CtrlMsg(target="EEG", action="START_STREAM").model_dump())
        self.ctrl_queues['PPG_INLET'].put(CtrlMsg(target="PPG", action="START_STREAM").model_dump())
        self.ctrl_queues['ANC_INLET'].put(CtrlMsg(target="Multi", action="START_STREAM").model_dump())

    def btn_stop_stream_cb(self):
        print("[GUI] Clicked Stop Stream")
        self.ctrl_queues['EEG_INLET_FILTER'].put(CtrlMsg(target="EEG", action="STOP_STREAM").model_dump())
        self.ctrl_queues['PPG_INLET'].put(CtrlMsg(target="PPG", action="STOP_STREAM").model_dump())
        self.ctrl_queues['ANC_INLET'].put(CtrlMsg(target="Multi", action="STOP_STREAM").model_dump())
    
    def btn_eeg_open_device_cb(self):
        if 'EEG' in self.cmd_mp_queues:
            if not self.is_eeg_connected:
                self.cmd_mp_queues['EEG'].put(CmdMsg(target="EEG", action="OPEN_DEVICE").model_dump())
                self.cmd_mp_queues['EEG'].put(CmdMsg(target="EEG", action="START_STREAM").model_dump())
            else:
                self.cmd_mp_queues['EEG'].put(CmdMsg(target='EEG', action='STOP_STREAM').model_dump())
                self.cmd_mp_queues['EEG'].put(CmdMsg(target='EEG', action='CLOSE_DEVICE').model_dump())
    
    def btn_emotibit_open_device_cb(self):
        if 'EMOTIBIT' in self.cmd_mp_queues:
            if not self.is_emotibit_connected:
                self.cmd_mp_queues['EMOTIBIT'].put(CmdMsg(target="EMOTIBIT", action="OPEN_DEVICE").model_dump())
                self.cmd_mp_queues['EMOTIBIT'].put(CmdMsg(target="EMOTIBIT", action="START_STREAM").model_dump())
            else:
                self.cmd_mp_queues['EMOTIBIT'].put(CmdMsg(target='EMOTIBIT', action='STOP_STREAM').model_dump())
                self.cmd_mp_queues['EMOTIBIT'].put(CmdMsg(target='EMOTIBIT', action='CLOSE_DEVICE').model_dump())

    def update_window_layouts(self):
        # ----- Monitor Tab Secondary Display (For Alpha and Beta Displays) -----#
        if dpg.does_item_exist("monitor_sec_display") and dpg.get_item_configuration("monitor_sec_display")['show']:
            parent_height = dpg.get_item_rect_size("monitor_sec_display")[1]
            
            # Subtracting height of spacers to prevent scroll bar from appearing.
            available_height = parent_height - 26
            
            # Ensure height doesn't drop below a minimum threshold
            if available_height > 20:
                half_height = available_height // 2
                
                # Apply the new 50% heights to the exact string tags
                dpg.configure_item("alpha_display", height=half_height)
                dpg.configure_item("beta_display", height=half_height)

        # ----- EEG Widget -----#
        channel_type = "eeg"       
        if dpg.does_item_exist(f"{channel_type}_plots_parent") and dpg.get_item_configuration(f"{channel_type}_plots_parent")['show']:
            eeg_group_plot_height = dpg.get_item_rect_size(f"{channel_type}_plots_parent")[1]

            visible_ch = [i for i in range(1, 9) if dpg.get_value(f"en_{channel_type}_ch{i}")]
            num_visible_ch = len(visible_ch)

            if available_height > 20 and num_visible_ch > 0:
                available_height = eeg_group_plot_height - 4*(num_visible_ch-1)
                portion_height = available_height // num_visible_ch
                remainder_height = available_height % num_visible_ch
                
                for channel_num in visible_ch:
                    item_tag = f"{channel_type}_ch{channel_num}_group_ch_plot"
                    if dpg.does_item_exist(item_tag):
                        if not channel_num == visible_ch[-1]:
                            dpg.configure_item(item_tag, height=portion_height)
                        else:
                            dpg.configure_item(item_tag, height=portion_height+remainder_height)

        # ----- PPG Widget -----#       
        channel_type = "ppg" 
        if dpg.does_item_exist(f"{channel_type}_plots_parent") and dpg.get_item_configuration(f"{channel_type}_plots_parent")['show']:
            eeg_group_plot_height = dpg.get_item_rect_size(f"{channel_type}_plots_parent")[1]
            num_visible_ch = 3

            if available_height > 20 and num_visible_ch > 0:
                available_height = eeg_group_plot_height - 4*(num_visible_ch-1)
                portion_height = available_height // num_visible_ch
                remainder_height = available_height % num_visible_ch
                
                for channel_num in range(1,4):
                    item_tag = f"{channel_type}_ch{channel_num}_group_ch_plot"
                    if dpg.does_item_exist(item_tag):
                        if not channel_num == 3:
                            dpg.configure_item(item_tag, height=portion_height)
                        else:
                            dpg.configure_item(item_tag, height=portion_height+remainder_height)
    

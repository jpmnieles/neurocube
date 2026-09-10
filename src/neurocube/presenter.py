import queue
from datetime import datetime
import dearpygui.dearpygui as dpg
from mne_lsl.lsl import local_clock

from models import ModelManager
from models import CtrlMsg
from views import MainView
from processes import CmdMsg

from widgets import EEGPlot, PPGPlot, TempPlot, GSRPlot, MarkerPlot


STIMULUS_MARKERS = {"A", "B", "C", "D", "E"}
MARKER_COLORS = {
    "stimulus": [255, 215, 0, 255],
    "keypress": [0, 255, 255, 255],
    "block": [255, 0, 255, 255],
}


class UiPresenter:
    def __init__(self, model: ModelManager, view: MainView,
                 cmd_mp_queues: dict, status_mp_queue, 
                 ctrl_queues:dict, display_queues: dict,
                 process_manager=None):
        
        # MVP Components
        self.model = model
        self.view = view

        # Queues
        self.cmd_mp_queues = cmd_mp_queues
        self.status_mp_queue = status_mp_queue
        self.ctrl_queues = ctrl_queues
        self.display_queues = display_queues

        # Process Manager
        self.process_manager = process_manager

        # Status Flags
        self.is_eeg_connected = False
        self.is_emotibit_connected = False
        self.is_psychopy_running = False
        self.is_recording = False
        self.is_streaming = True
        self.marker_lines = []

    def setup_callbacks(self):
        """Setup Model Callbacks"""
        dpg.set_item_callback("stream_toggle_btn", self.btn_stream_toggle_cb)
        dpg.set_item_callback("btn_eeg_device_connect", self.btn_eeg_open_device_cb)
        dpg.set_item_callback("btn_emotibit_device_connect", self.btn_emotibit_open_device_cb)
        dpg.set_item_callback("recorder_toggle_btn", self.btn_recorder_toggle_cb)
        dpg.set_item_callback("psychopy_run_btn", self.btn_psychopy_run_cb)
        dpg.set_item_callback("experiment_select", self.experiment_select_cb)
        dpg.set_item_callback("erp_browse_btn", self.erp_browse_cb)
        dpg.set_item_callback("erp_file_dialog", self.erp_file_selected_cb)
        dpg.set_item_callback("erp_load_btn", self.erp_load_cb)


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

            # Timing
            window_start_time = local_clock()

            # Thread Functions
            self.process_status_mp_queue()
            self.process_status_mthread_queue()
            self.process_eeg_time_series_widget(window_start_time)
            self.process_ppg_time_series_widget(window_start_time)
            self.process_temp_time_series_widget(window_start_time)
            self.process_gsr_time_series_widget(window_start_time)
            self.process_marker_time_series_widget(window_start_time)

            self.view.widgets.widgets["PBM_widget"].update_timer()
            
            dpg.render_dearpygui_frame()  # Throttling based on the Monitor Refresh Rate

    def process_temp_time_series_widget(self, window_start_time):
        while True:
            new_data = False
            try:
                data, timestamps = self.display_queues['TEMP_TIME'].get_nowait()
                new_data = True
                # print(f'[GUI TEMP Display] Data In, Time: {datetime.now()}')
                # print(f'[GUI TEMP Display] timestamps: {timestamps[-5:]}')
            except queue.Empty:
                break

            if new_data:
                # Relative Timestamps
                rel_timestamps =  timestamps - window_start_time
                rel_timestamps_list = rel_timestamps.tolist()

                is_auto = True

                if is_auto:
                    window_time_str = dpg.get_value("combo_temp_time_window")
                    WINDOW_TIME = TempPlot.combo2twindow_dict[window_time_str]
                    time_mask = rel_timestamps > -WINDOW_TIME

                # Process only channel which are enabled
                channel_num = 1
                data_list = data.tolist()
                data_bottom_list = (data-99999).tolist()
                dpg.set_value(f"temp_ch{channel_num}_series", [rel_timestamps_list, data_list])
                dpg.set_value(f"temp_ch{channel_num}_shade", [rel_timestamps_list, data_list, data_bottom_list])

                if is_auto:
                    data_filtered = data[time_mask]

                    # ADD THIS SAFETY CHECK
                    if data_filtered.size > 0:
                        max_data_filtered = data_filtered.max()
                        min_data_filtered = data_filtered.min()
                        dpg.set_value("Temp_widget_data_text", f"{data_filtered.mean():2.2f}°C")
                        dpg.set_axis_limits(f"temp_ch{channel_num}_x_axis", -WINDOW_TIME  , 0)
                        dpg.set_axis_limits(f"temp_ch{channel_num}_y_axis", 
                            min_data_filtered, max_data_filtered)
                        dpg.configure_item(f"temp_ch{channel_num}_max_y_axis", label=f"{max_data_filtered:.2f}")
                        dpg.configure_item(f"temp_ch{channel_num}_min_y_axis", label=f"{min_data_filtered:.2f}")

    def process_eeg_time_series_widget(self, window_start_time):
        while True:
            new_data = False
            try:
                data, timestamps = self.display_queues['EEG_TIME'].get_nowait()
                new_data = True
                # print(f'[GUI Display] Data In, Time: {datetime.now()}')
                # print(f'[GUI Display] timestamps: {timestamps[-5:]}')
            except queue.Empty:
                break

            if new_data:
                # Relative Timestamps
                rel_timestamps =  timestamps - window_start_time
                rel_timestamps_list = rel_timestamps.tolist()

                vert_scale = dpg.get_value("combo_vert_scale")
                is_auto = (vert_scale == 'Auto')

                if is_auto:
                    window_time_str = dpg.get_value("combo_time_window")
                    WINDOW_TIME = EEGPlot.combo2twindow_dict[window_time_str]
                    time_mask = rel_timestamps > -WINDOW_TIME

                # print(f'[GUI Display] RELATIVE TIMESTAMP {rel_timestamps[-1]}')
                
                # Process only channel which are enabled
                for channel_num in range(1,9):
                    if dpg.get_value(f"en_eeg_ch{channel_num}"):
                        dpg.set_value(f"eeg_ch{channel_num}_series", [rel_timestamps_list, data[channel_num-1].tolist()])

                        if is_auto:
                            data_filtered = data[channel_num - 1][time_mask]

                            # ADD THIS SAFETY CHECK
                            if data_filtered.size > 0:
                                max_data_filtered = data_filtered.max()
                                min_data_filtered = data_filtered.min()
                                dpg.set_axis_limits(f"eeg_ch{channel_num}_y_axis", 
                                    min_data_filtered, max_data_filtered)
                                dpg.configure_item(f"eeg_ch{channel_num}_max_y_axis", label=f"{max_data_filtered:.2f}")
                                dpg.configure_item(f"eeg_ch{channel_num}_min_y_axis", label=f"{min_data_filtered:.2f}")
                            
    def process_ppg_time_series_widget(self, window_start_time):
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

                        # ADD THIS SAFETY CHECK
                        if data_filtered.size > 0:
                            max_data_filtered = data_filtered.max()
                            min_data_filtered = data_filtered.min()
                            dpg.set_axis_limits(f"ppg_ch{channel_num}_y_axis", 
                                min_data_filtered, max_data_filtered)
                            dpg.configure_item(f"ppg_ch{channel_num}_max_y_axis", label=f"{max_data_filtered:.2f}")
                            dpg.configure_item(f"ppg_ch{channel_num}_min_y_axis", label=f"{min_data_filtered:.2f}")

    def process_gsr_time_series_widget(self, window_start_time):
        while True:
            new_data = False
            try:
                data, timestamps = self.display_queues['GSR_TIME'].get_nowait()
                new_data = True
            except queue.Empty:
                break

            if new_data:
                # Relative Timestamps
                rel_timestamps =  timestamps - window_start_time
                rel_timestamps_list = rel_timestamps.tolist()

                is_auto = True

                if is_auto:
                    window_time_str = dpg.get_value("combo_gsr_time_window")
                    WINDOW_TIME = GSRPlot.combo2twindow_dict[window_time_str]
                    time_mask = rel_timestamps > -WINDOW_TIME

                # Process only channel which are enabled
                channel_num = 2
                data_list = data.tolist()
                data_bottom_list = (data-99999).tolist()
                dpg.set_value(f"gsr_ch{channel_num}_series", [rel_timestamps_list, data_list])
                dpg.set_value(f"gsr_ch{channel_num}_shade", [rel_timestamps_list, data_list, data_bottom_list])

                if is_auto:
                    data_filtered = data[time_mask]

                    # ADD THIS SAFETY CHECK
                    if data_filtered.size > 0:
                        max_data_filtered = data_filtered.max()
                        min_data_filtered = data_filtered.min()
                        dpg.set_value("GSR_widget_data_text", f"{data_filtered.mean():2.2f}uS")
                        dpg.set_axis_limits(f"gsr_ch{channel_num}_x_axis", -WINDOW_TIME  , 0)
                        dpg.set_axis_limits(f"gsr_ch{channel_num}_y_axis", 
                            min_data_filtered, max_data_filtered)
                        dpg.configure_item(f"gsr_ch{channel_num}_max_y_axis", label=f"{max_data_filtered:.2f}")
                        dpg.configure_item(f"gsr_ch{channel_num}_min_y_axis", label=f"{min_data_filtered:.2f}")                    

    def process_marker_time_series_widget(self, window_start_time):
        if not self.is_streaming:
            return

        window_label = dpg.get_value("combo_marker_time_window")
        window_time = MarkerPlot.combo2twindow_dict[window_label]
        max_window_time = 20

        while True:
            try:
                marker_values, timestamps = self.display_queues["MARKER_TIME"].get_nowait()
            except queue.Empty:
                break

            for marker_value, timestamp in zip(marker_values, timestamps):
                marker_time = float(timestamp)
                relative_time = marker_time - window_start_time
                line_color = self._marker_color(marker_value)
                line_id = dpg.add_drag_line(
                    label="", default_value=relative_time, color=line_color,
                    vertical=True, parent="marker_ch1_plot"
                )
                annotation_id = dpg.add_plot_annotation(
                    label=marker_value, default_value=(relative_time, 0.0),
                    offset=(8, 0), color=line_color, clamped=False,
                    parent="marker_ch1_plot"
                )
                self.marker_lines.append((marker_time, line_id, annotation_id))
                dpg.set_value("Marker_widget_data_text", f"Marker: {marker_value}")

        active_lines = []
        for timestamp, line_id, annotation_id in self.marker_lines:
            relative_timestamp = timestamp - window_start_time
            if relative_timestamp < -max_window_time:
                for item_id in (line_id, annotation_id):
                    if dpg.does_item_exist(item_id):
                        dpg.delete_item(item_id)
                continue

            if dpg.does_item_exist(line_id):
                dpg.set_value(line_id, relative_timestamp)
                dpg.set_value(annotation_id, [relative_timestamp, 0.0])
                active_lines.append((timestamp, line_id, annotation_id))

        self.marker_lines = active_lines
        dpg.set_axis_limits("marker_ch1_x_axis", -window_time, 0)

    @staticmethod
    def _marker_color(marker_value):
        if marker_value.startswith("Block_"):
            return MARKER_COLORS["block"]
        if marker_value in STIMULUS_MARKERS:
            return MARKER_COLORS["stimulus"]
        return MARKER_COLORS["keypress"]

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
                        self.ctrl_queues['EEG_INLET_FILTER'].put(
                            CtrlMsg(target="EEG", action="START_STREAM").model_dump()
                        )
                        dpg.configure_item("btn_eeg_device_connect", label="Stop Device", enabled=True)
                    elif status_msg['state'] == "CLOSE_DEVICE":
                        self.is_eeg_connected = False
                        self.ctrl_queues['EEG_INLET_FILTER'].put(
                            CtrlMsg(target="EEG", action="STOP_STREAM").model_dump()
                        )
                        dpg.configure_item("btn_eeg_device_connect", label="Start Device", enabled=True)
                    elif status_msg['state'] in ("ERROR", "EXIT"):
                        self.is_eeg_connected = False
                        dpg.set_value("btn_eeg_device_connect_status", "Disconnected")
                        dpg.configure_item(
                            "btn_eeg_device_connect_indicator",
                            color=[128, 128, 128, 255],
                            fill=[128, 128, 128, 255],
                        )
                        dpg.configure_item(
                            "btn_eeg_device_connect",
                            label="Start Device",
                            enabled=True,
                        )

                    if self.is_eeg_connected:
                        dpg.set_value("btn_eeg_device_connect"+"_status", "Connected")
                        dpg.configure_item("btn_eeg_device_connect"+"_indicator",color=[0, 255, 0, 255], fill=[0, 255, 0, 255])
                        dpg.configure_item("btn_eeg_device_connect", label="Stop Device", enabled=True)
                    else:
                        dpg.set_value("btn_eeg_device_connect"+"_status", "Disconnected")
                        dpg.configure_item("btn_eeg_device_connect"+"_indicator", color=[128, 128, 128, 255], fill=[128, 128, 128, 255])
                        if status_msg['state'] == "CLOSE_DEVICE":
                            dpg.configure_item("btn_eeg_device_connect", label="Start Device", enabled=True)
                
                ### Status Messages ###
                if status_msg['source'] == "EMOTIBIT":

                    # Classifying Messages
                    if status_msg['state'] == "START_STREAM":
                        self.is_emotibit_connected = True
                        self.ctrl_queues['PPG_INLET'].put(
                            CtrlMsg(target="PPG", action="START_STREAM").model_dump()
                        )
                        self.ctrl_queues['ANC_INLET'].put(
                            CtrlMsg(target="Multi", action="START_STREAM").model_dump()
                        )
                        dpg.configure_item("btn_emotibit_device_connect", label="Stop Device", enabled=True)
                    elif status_msg['state'] == "CLOSE_DEVICE":
                        self.is_emotibit_connected = False
                        self.ctrl_queues['PPG_INLET'].put(
                            CtrlMsg(target="PPG", action="STOP_STREAM").model_dump()
                        )
                        self.ctrl_queues['ANC_INLET'].put(
                            CtrlMsg(target="Multi", action="STOP_STREAM").model_dump()
                        )
                        dpg.configure_item("btn_emotibit_device_connect", label="Start Device", enabled=True)
                    elif status_msg['state'] in ("ERROR", "EXIT"):
                        self.is_emotibit_connected = False
                        dpg.set_value("btn_emotibit_device_connect_status", "Disconnected")
                        dpg.configure_item(
                            "btn_emotibit_device_connect_indicator",
                            color=[128, 128, 128, 255],
                            fill=[128, 128, 128, 255],
                        )
                        dpg.configure_item(
                            "btn_emotibit_device_connect",
                            label="Start Device",
                            enabled=True,
                        )

                    if self.is_emotibit_connected:
                        dpg.set_value("btn_emotibit_device_connect"+"_status", "Connected")
                        dpg.configure_item("btn_emotibit_device_connect"+"_indicator",color=[0, 255, 0, 255], fill=[0, 255, 0, 255])
                        dpg.configure_item("btn_emotibit_device_connect", label="Stop Device", enabled=True)
                    else:
                        dpg.set_value("btn_emotibit_device_connect"+"_status", "Disconnected")
                        dpg.configure_item("btn_emotibit_device_connect"+"_indicator", color=[128, 128, 128, 255], fill=[128, 128, 128, 255])
                        if status_msg['state'] == "CLOSE_DEVICE":
                            dpg.configure_item("btn_emotibit_device_connect", label="Start Device", enabled=True)

                ### Status Messages ###
                if status_msg['source'] == "PSYCHOPY":
                    
                    if status_msg['state'] == "START":
                        self.is_psychopy_running = True
                        dpg.set_value("psychopy_status", "Running")
                        dpg.configure_item("psychopy_indicator", color=[0, 255, 0, 255], fill=[0, 255, 0, 255])
                        dpg.configure_item("psychopy_run_btn", label="Stop Experiment", enabled=True)
                        dpg.configure_item("experiment_select", enabled=False)
                    elif status_msg['state'] == "EXIT":
                        self.is_psychopy_running = False
                        dpg.set_value("psychopy_status", "Ready")
                        dpg.configure_item("psychopy_indicator", color=[128, 128, 128, 255], fill=[128, 128, 128, 255])
                        dpg.configure_item("psychopy_run_btn", label="Start Experiment", enabled=True)
                        dpg.configure_item("experiment_select", enabled=True)
                        if self.process_manager:
                            self.process_manager.stop_process("PSYCHOPY")
                    elif status_msg['state'] == "ERROR":
                        self.is_psychopy_running = False
                        dpg.set_value("psychopy_status", "Error")
                        dpg.configure_item("psychopy_indicator", color=[255, 0, 0, 255], fill=[255, 0, 0, 255])
                        dpg.configure_item("psychopy_run_btn", label="Start Experiment", enabled=True)
                        dpg.configure_item("experiment_select", enabled=True)
                        if self.process_manager:
                            self.process_manager.stop_process("PSYCHOPY")


            except queue.Empty:
                break  # No more multiprocessing status messages

    def process_status_mthread_queue(self):
        """Process status messages generated by ModelManager threads."""
        while True:
            try:
                status_msg = self.model.status_queue.get_nowait()
                log_entry = f"[{status_msg['source']}] {status_msg['state']}: {status_msg['message']}\n"

                current_items = dpg.get_value("log_stream")
                dpg.set_value("log_stream", current_items + log_entry)
                dpg.set_y_scroll("status_window", 999999)

                if status_msg['source'] == "ERP":
                    if status_msg['state'] == "RESULT":
                        result = status_msg['data']
                        times = result["times_ms"]
                        erp_data = result["erp_data"]
                        dpg.set_value("erp_target_series", [times, erp_data.get("Target", [])])
                        dpg.set_value("erp_standard_series", [times, erp_data.get("Standard", [])])
                        dpg.configure_item("erp_x_axis", auto_fit=True)
                        dpg.configure_item("erp_y_axis", auto_fit=True)
                    elif status_msg['state'] == "ERROR":
                        print(f"[ERP] ERROR: {status_msg['message']}")
                    continue

                if status_msg['source'] != "RECORDER":
                    continue

                if status_msg['state'] == "START_RECORD":
                    self.is_recording = True
                    dpg.set_value("recorder_status", "Recording")
                    dpg.configure_item("recorder_toggle_btn", label="Stop Recording", enabled=True)
                    dpg.configure_item("recorder_indicator", color=[0, 255, 0, 255], fill=[0, 255, 0, 255])
                elif status_msg['state'] == "STOP_RECORD":
                    self.is_recording = False
                    dpg.set_value("recorder_status", "Ready")
                    dpg.configure_item("recorder_toggle_btn", label="Start Recording", enabled=True)
                    dpg.configure_item("recorder_indicator", color=[128, 128, 128, 255], fill=[128, 128, 128, 255])
                elif status_msg['state'] == "ERROR":
                    self.is_recording = False
                    dpg.set_value("recorder_status", "Error")
                    dpg.configure_item("recorder_toggle_btn", label="Start Recording", enabled=True)
                    dpg.configure_item("recorder_indicator", color=[255, 0, 0, 255], fill=[255, 0, 0, 255])

            except queue.Empty:
                break  # No more ModelManager thread status messages

    def erp_browse_cb(self):
        dpg.show_item("erp_file_dialog")

    @staticmethod
    def erp_file_selected_cb(sender, app_data, user_data):
        file_path = app_data.get("file_path_name", "") if isinstance(app_data, dict) else ""
        if file_path:
            dpg.set_value("erp_file_path", file_path)

    def erp_load_cb(self):
        file_path = dpg.get_value("erp_file_path").strip()
        if not file_path:
            print("[ERP] Select an XDF file first")
            return

        self.ctrl_queues["ERP"].put(CtrlMsg(
            target="ERP",
            action="PROCESS",
            data={"file_path": file_path},
        ).model_dump())

    ### Callbacks ###
    
    def btn_stream_toggle_cb(self):
        if self.is_streaming:
            print("[GUI] Clicked Pause Stream")
            self.is_streaming = False
            action = "STOP_STREAM"
            label = "Start Stream"
            theme = "green_btn_theme"
        else:
            print("[GUI] Clicked Start Stream")
            self.is_streaming = True
            action = "START_STREAM"
            label = "Pause Stream"
            theme = "yellow_btn_theme"

        dpg.configure_item("stream_toggle_btn", label=label)
        dpg.bind_item_theme("stream_toggle_btn", theme)
        self.ctrl_queues['EEG_INLET_FILTER'].put(CtrlMsg(target="EEG", action=action).model_dump())
        self.ctrl_queues['PPG_INLET'].put(CtrlMsg(target="PPG", action=action).model_dump())
        self.ctrl_queues['ANC_INLET'].put(CtrlMsg(target="Multi", action=action).model_dump())
        self.ctrl_queues['MARKER_INLET'].put(CtrlMsg(target="Markers", action=action).model_dump())

    def btn_recorder_toggle_cb(self):
        if self.is_recording:
            dpg.configure_item("recorder_toggle_btn", label="Stopping...", enabled=False)
            self.ctrl_queues['RECORDER'].put(
                CtrlMsg(target="RECORDER", action="STOP", data={}).model_dump()
            )
            return

        recording_data = {
            "subject": dpg.get_value("recorder_subject").strip(),
            "session": dpg.get_value("recorder_session").strip(),
            "task": dpg.get_value("recorder_task").strip(),
            "run": dpg.get_value("recorder_run").strip(),
        }
        if not all(recording_data.values()):
            self._set_recorder_error("Subject, session, task, and run are required")
            return

        dpg.configure_item("recorder_toggle_btn", label="Starting...", enabled=False)
        dpg.set_value("recorder_status", "Starting")
        dpg.configure_item(
            "recorder_indicator",
            color=[255, 200, 0, 255], fill=[255, 200, 0, 255]
        )
        self.ctrl_queues['RECORDER'].put(
            CtrlMsg(target="RECORDER", action="START", data=recording_data).model_dump()
        )

    def _set_recorder_error(self, message):
        self.is_recording = False
        dpg.set_value("recorder_status", "Error")
        dpg.configure_item("recorder_toggle_btn", label="Start Recording", enabled=True)
        dpg.configure_item(
            "recorder_indicator",
            color=[255, 0, 0, 255], fill=[255, 0, 0, 255]
        )
        current_items = dpg.get_value("log_stream")
        dpg.set_value("log_stream", current_items + f"[RECORDER] ERROR: {message}\n")
    
    def btn_eeg_open_device_cb(self):
        if 'EEG' in self.cmd_mp_queues:
            if not self.is_eeg_connected:
                dpg.configure_item("btn_eeg_device_connect", label="Starting...", enabled=False)
                # 1. Spin up the OS Process
                if self.process_manager:
                    self.process_manager.start_process("EEG")
                
                # 2. Send commands to the newly created process
                self.cmd_mp_queues['EEG'].put(CmdMsg(target="EEG", action="OPEN_DEVICE").model_dump())
                self.cmd_mp_queues['EEG'].put(CmdMsg(target="EEG", action="START_STREAM").model_dump())
            else:
                dpg.configure_item("btn_eeg_device_connect", label="Stopping...", enabled=False)
                # 1. Send graceful hardware shutdown commands
                self.cmd_mp_queues['EEG'].put(CmdMsg(target='EEG', action='STOP_STREAM').model_dump())
                self.cmd_mp_queues['EEG'].put(CmdMsg(target='EEG', action='CLOSE_DEVICE').model_dump())
                
                # 2. Kill the OS Process
                if self.process_manager:
                    self.process_manager.stop_process("EEG")
    
    def btn_emotibit_open_device_cb(self):
        if 'EMOTIBIT' in self.cmd_mp_queues:
            if not self.is_emotibit_connected:
                dpg.configure_item("btn_emotibit_device_connect", label="Starting...", enabled=False)
                # 1. Spin up the OS Process
                if self.process_manager:
                    self.process_manager.start_process("EMOTIBIT")
                
                # 2. Send commands to the newly created process
                self.cmd_mp_queues['EMOTIBIT'].put(CmdMsg(target="EMOTIBIT", action="OPEN_DEVICE").model_dump())
                self.cmd_mp_queues['EMOTIBIT'].put(CmdMsg(target="EMOTIBIT", action="START_STREAM").model_dump())
            else:
                dpg.configure_item("btn_emotibit_device_connect", label="Stopping...", enabled=False)
                # 1. Send graceful hardware shutdown commands
                self.cmd_mp_queues['EMOTIBIT'].put(CmdMsg(target='EMOTIBIT', action='STOP_STREAM').model_dump())
                self.cmd_mp_queues['EMOTIBIT'].put(CmdMsg(target='EMOTIBIT', action='CLOSE_DEVICE').model_dump())
                
                # 2. Kill the OS Process
                if self.process_manager:
                    self.process_manager.stop_process("EMOTIBIT")

    def btn_psychopy_run_cb(self):
        if not self.process_manager:
            return

        if self.is_psychopy_running:
            dpg.configure_item("psychopy_run_btn", label="Stopping...", enabled=False)
            self.process_manager.stop_process("PSYCHOPY")
            self.is_psychopy_running = False
            dpg.set_value("psychopy_status", "Ready")
            dpg.configure_item(
                "psychopy_indicator",
                color=[128, 128, 128, 255],
                fill=[128, 128, 128, 255],
            )
            dpg.configure_item("psychopy_run_btn", label="Start Experiment", enabled=True)
            dpg.configure_item("experiment_select", enabled=True)
            return

        self.is_psychopy_running = True
        dpg.set_value("psychopy_status", "Starting")
        dpg.configure_item("psychopy_indicator", color=[255, 200, 0, 255], fill=[255, 200, 0, 255])
        dpg.configure_item("psychopy_run_btn", label="Starting...", enabled=False)
        dpg.configure_item("experiment_select", enabled=False)
        experiment_name = dpg.get_value("experiment_select")
        experiment_module = self.view.device_panel.experiments[experiment_name]
        self.process_manager.start_process("PSYCHOPY", experiment_module=experiment_module)

    def experiment_select_cb(self, sender, app_data, user_data):
        dpg.set_value("psychopy_experiment_name", app_data)

    def update_window_layouts(self):
        # ----- Monitor Tab Secondary Display (For Alpha and Beta Displays) -----#
        if self.view.active_tab == "monitor_tab" and dpg.does_item_exist("monitor_sec_display"):
            parent_height = dpg.get_item_rect_size("monitor_sec_display")[1]
            
            # Subtracting height of spacers to prevent scroll bar from appearing.
            available_height = parent_height - 26
            
            # Ensure height doesn't drop below a minimum threshold
            if available_height > 20:
                half_height = available_height // 2
                
                # Apply the new 50% heights to the exact string tags
                dpg.configure_item("alpha_display", height=half_height)
                dpg.configure_item("beta_display", height=half_height)

        # ----- PsychoPy Tab Secondary Displays -----#
        if self.view.active_tab == "psychopy_tab" and dpg.does_item_exist("exp_sec_display"):
            parent_height = dpg.get_item_rect_size("exp_sec_display")[1]

            # Reserve space for the spacers, separator, and child-window padding.
            available_height = parent_height - 26

            if available_height > 20:
                alpha_height = int(available_height * 0.25)
                beta_height = available_height - alpha_height
                dpg.configure_item("exp_alpha_display", height=alpha_height)
                dpg.configure_item("exp_beta_display", height=beta_height)

        # ----- EEG Widget -----#
        channel_type = "eeg"       
        if dpg.does_item_exist(f"{channel_type}_plots_parent") and dpg.get_item_configuration(f"{channel_type}_plots_parent")['show']:
            eeg_group_plot_height = dpg.get_item_rect_size(f"{channel_type}_plots_parent")[1]

            visible_ch = [i for i in range(1, 9) if dpg.get_value(f"en_{channel_type}_ch{i}")]
            num_visible_ch = len(visible_ch)

            if eeg_group_plot_height > 20 and num_visible_ch > 0:
                available_plot_height = eeg_group_plot_height - 4*(num_visible_ch-1)
                portion_height = available_plot_height // num_visible_ch
                remainder_height = available_plot_height % num_visible_ch
                
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
            ppg_group_plot_height = dpg.get_item_rect_size(f"{channel_type}_plots_parent")[1]
            num_visible_ch = 3

            if ppg_group_plot_height > 20 and num_visible_ch > 0:
                available_plot_height = ppg_group_plot_height - 4*(num_visible_ch-1)
                portion_height = available_plot_height // num_visible_ch
                remainder_height = available_plot_height % num_visible_ch
                
                for channel_num in range(1,4):
                    item_tag = f"{channel_type}_ch{channel_num}_group_ch_plot"
                    if dpg.does_item_exist(item_tag):
                        if not channel_num == 3:
                            dpg.configure_item(item_tag, height=portion_height)
                        else:
                            dpg.configure_item(item_tag, height=portion_height+remainder_height)

        # ----- Marker Widget -----#
        channel_type = "marker"
        if dpg.does_item_exist(f"{channel_type}_plots_parent") and dpg.get_item_configuration(f"{channel_type}_plots_parent")['show']:
            marker_group_plot_height = dpg.get_item_rect_size(f"{channel_type}_plots_parent")[1]
            item_tag = f"{channel_type}_ch1_group_ch_plot"

            if marker_group_plot_height > 20 and dpg.does_item_exist(item_tag):
                dpg.configure_item(item_tag, height=marker_group_plot_height)
    

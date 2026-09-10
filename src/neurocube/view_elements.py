import math
import time
import dearpygui.dearpygui as dpg
from utils import PrecisionTimer


class IndicatorStatus:
    """Reusable status label and colored indicator for a controllable component."""

    _STATES = {
        "disconnected": ("Disconnected", [128, 128, 128, 255]),
        "ready": ("Ready", [128, 128, 128, 255]),
        "connected": ("Connected", [0, 255, 0, 255]),
        "running": ("Running", [0, 255, 0, 255]),
        "recording": ("Recording", [0, 255, 0, 255]),
        "starting": ("Starting", [255, 200, 0, 255]),
        "error": ("Error", [255, 0, 0, 255]),
    }

    def __init__(self, tag_prefix, initial_state="ready"):
        self.status_tag = f"{tag_prefix}_status"
        self.indicator_tag = f"{tag_prefix}_indicator"
        self.state = initial_state

    def build(self):
        with dpg.group(horizontal=True):
            with dpg.drawlist(width=16, height=20):
                dpg.draw_circle(
                    center=[8, 10],
                    radius=5,
                    color=[128, 128, 128, 255],
                    fill=[128, 128, 128, 255],
                    tag=self.indicator_tag,
                )
            dpg.add_text(tag=self.status_tag, color=[160, 160, 160])

        self.set_state(self.state)

    def set_state(self, state):
        """Update the component state and its visible label and indicator."""
        if state not in self._STATES:
            raise ValueError(f"Unknown indicator state: {state}")

        label, color = self._STATES[state]
        self.state = state
        dpg.set_value(self.status_tag, label)
        dpg.configure_item(self.indicator_tag, color=color, fill=color)


class DeviceBlock:
    """A self-contained hardware control component."""
    def __init__(self, device_name, btn_tag):
        self.device_name = device_name
        self.btn_tag = btn_tag
        self.status = IndicatorStatus(btn_tag, initial_state="disconnected")
        self.status_tag = self.status.status_tag
        self.indicator_tag = self.status.indicator_tag

    def build(self):
        with dpg.group():
            # Add text and button
            dpg.add_text(self.device_name, color=[255, 255, 255])
            dpg.add_button(label="Start Device", width=-1, tag=self.btn_tag)
            
            self.status.build()
                
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)


class ExperimentBlock:
    """Experiment selector and process control component."""
    def __init__(self, experiments, combo_tag="experiment_select"):
        self.experiments = experiments
        self.combo_tag = combo_tag
        self.btn_tag = "psychopy_run_btn"
        self.status = IndicatorStatus("psychopy", initial_state="ready")
        self.status_tag = self.status.status_tag
        self.indicator_tag = self.status.indicator_tag

    def build(self):
        with dpg.group():
            dpg.add_combo(
                items=list(self.experiments),
                default_value=list(self.experiments)[0],
                tag=self.combo_tag,
                width=-1,
            )
            dpg.add_spacer(height=2)
            dpg.add_button(label="Start Experiment", width=-1, tag=self.btn_tag)

            self.status.build()

            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)


class LabRecorderWidget:
    """Controls LabRecorder metadata and recording state."""
    def __init__(self):
        self.button_tag = "recorder_toggle_btn"
        self.timer = None
        self.recording_active = False
        self.recording_started_at = 0.0

    def build(self):
        self.build_metadata()
        self.build_controls()

    def build_metadata(self):
        dpg.add_text("RECORDING", color=[150, 150, 255])
        dpg.add_separator()

        dpg.add_text("Subject")
        dpg.add_input_text(tag="recorder_subject", default_value="S001", width=-1)
        dpg.add_text("Session")
        dpg.add_input_text(tag="recorder_session", default_value="DAY1", width=-1)
        dpg.add_text("Task")
        dpg.add_input_text(tag="recorder_task", default_value="ERP", width=-1)
        dpg.add_text("Run")
        dpg.add_input_text(tag="recorder_run", default_value="001", width=-1)

    def build_controls(self):
        dpg.add_spacer(height=10)
        dpg.add_button(label="Start Recording", tag=self.button_tag, height=35, width=-1)
        dpg.bind_item_theme(self.button_tag, "red_btn_theme")

        with dpg.child_window(
            tag="recorder_timer_box", width=-1, height=35,
            border=True, no_scrollbar=True,
        ):
            dpg.add_text("00:00:00", tag="recorder_timer_text", pos=(20, 7))
            dpg.bind_item_font("recorder_timer_text", "dynamic_font_16")

    def start_timer(self):
        if self.timer is not None:
            self.timer.cancel()

        self.timer = PrecisionTimer(interval=24 * 60 * 60)
        self.timer.start()
        self.update_timer()

    def set_recording_active(self, active):
        self.recording_active = active
        self.recording_started_at = time.monotonic()
        dpg.bind_item_theme(self.button_tag, "red_btn_theme")

    def update_recording_visual(self):
        if not self.recording_active:
            return

        elapsed = time.monotonic() - self.recording_started_at
        phase = (elapsed * 1.25 * 2 * math.pi) % (2 * math.pi)
        brightness = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(phase))
        theme_index = min(31, int((brightness - 0.55) / 0.45 * 31))
        dpg.bind_item_theme(
            self.button_tag,
            f"recording_btn_theme_{theme_index}",
        )

    def stop_timer(self, reset=True):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = None
        if reset:
            dpg.set_value("recorder_timer_text", "00:00:00")

    def update_timer(self):
        if self.timer is not None:
            total_seconds = max(0, int(self.timer.elapsed()))
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            dpg.set_value(
                "recorder_timer_text",
                f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            )
        self.center_timer_text()

    def center_timer_text(self):
        box_width, box_height = dpg.get_item_rect_size("recorder_timer_box")
        text_size = dpg.get_text_size(
            dpg.get_value("recorder_timer_text"), font="dynamic_font_16"
        )
        if text_size is None:
            return

        text_width, text_height = text_size
        dpg.configure_item(
            "recorder_timer_text",
            pos=(max(0, (box_width - text_width) / 2), max(0, (box_height - text_height) / 2)),
        )


class ComboDisplayWidget:
    def __init__(self, combo_item_list=[], widget_list=[], display_tag=''):
        self.combo_item_list = combo_item_list
        self.widget_list = widget_list
        self.display_tag = display_tag
        self.selected_value = ''
        self.combo2widget_dict = self._make_combo2widget_map(combo_item_list, widget_list)
        self.widget2combo_dict = self._make_widget2combo_map(widget_list, combo_item_list)

    def _make_combo2widget_map(self, combo_item_list, widget_list):
        map_dict = dict(zip(combo_item_list, widget_list))
        map_dict[''] = ''
        return map_dict
    
    def _make_widget2combo_map(self, widget_list, combo_item_list):
        map_dict = dict(zip(widget_list, combo_item_list))
        map_dict[''] = ''
        return map_dict
    
    def _get_child_widget(self, parent_tag):
        all_children = dpg.get_item_children(parent_tag, slot=1)
        
        # Look for any group or child container that contains a tracked child window
        for child in all_children:
            child_tag = dpg.get_item_alias(child)
            if child_tag in self.widget_list:
                return child_tag
        
        return ''

    def dropdown_callback(self, sender, app_data, user_data):
        """
        sender: The tag of the combo box that was clicked
        app_data: The string value selected in the dropdown (e.g., 'Child Window 4')  # Widget
        user_data: The tag of the parent display window hosting this combo box  # Tag of the Parent
        """
        self.selected_value = app_data
        dpg.set_value(sender, app_data)
        chosen_child_tag = self.combo2widget_dict[app_data]
        source_display_tag = dpg.get_item_parent(chosen_child_tag)
        target_display_tag = user_data
        old_child_tag = self._get_child_widget(target_display_tag)

        # If the chosen child is already in the target display, no change is needed
        if source_display_tag == target_display_tag:
            return
        
        # Changes in the system
        if old_child_tag:
            dpg.move_item(old_child_tag, parent=source_display_tag)
        dpg.move_item(chosen_child_tag, parent=target_display_tag)

        # Combo Box Change if not from Hidden Stage
        if not source_display_tag == "hidden_stage":
            dpg.set_value(f"combo_{source_display_tag}", self.widget2combo_dict[old_child_tag])

    def build(self, default_value=''):
        dpg.add_combo(items=self.combo_item_list, tag=f"combo_{self.display_tag}",
                        callback=self.dropdown_callback, user_data=self.display_tag, 
                        default_value=default_value, width=200)
        if default_value:
            self.dropdown_callback(f"combo_{self.display_tag}", default_value, self.display_tag)

    def activate(self):
        combo_tag = f"combo_{self.display_tag}"
        if self.selected_value and not dpg.get_value(combo_tag):
            self.dropdown_callback(
                combo_tag, self.selected_value, self.display_tag
            )


class DynamicPlot:
    """A self-contained plotting widget that handles its own axes and data updates."""
    def __init__(self, tag, default_sensor="EEG", height=-1, parent=0):
        self.tag = tag
        self.sensor_type = default_sensor
        self.height = height
        self.parent = parent
        
        self.series_id = None
        self.x_axis_id = None
        self.y_axis_id = None

        self.build()
        x, y = self._generate_dummy_data(default_sensor)
        self.update_plot(default_sensor, x, y)

    def _generate_dummy_data(self, sensor_type):  # For Testing
        """Generates distinct mathematical waves to simulate live hardware data."""
        x = [i * 0.1 for i in range(100)]
        if sensor_type == "EEG":
            y = [math.sin(i * 0.5) + math.sin(i * 2.0) * 0.3 for i in range(100)]
        elif sensor_type == "PPG":
            y = [math.sin(i * 0.2) * 2.0 for i in range(100)]
        elif sensor_type == "IMU":
            y = [math.cos(i * 0.1) for i in range(100)]
        else:
            y = [0 for _ in range(100)]
        return x, y

    def build(self):
        # We now use self.height to control the vertical space
        with dpg.child_window(tag=self.tag, border=True, height=self.height, width=-1, parent=self.parent):
            with dpg.plot(height=-1, width=-1):
                dpg.add_plot_legend()
                
                self.x_axis_id = dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                self.y_axis_id = dpg.add_plot_axis(dpg.mvYAxis, label="Amplitude")
                
                self.series_id = dpg.add_line_series(
                    [], [], 
                    label=f"{self.sensor_type} Data", 
                    parent=self.y_axis_id
                )

    def update_plot(self, sensor_type, x_data, y_data):
        """Pushes new data to the plot and auto-fits the view."""
        self.sensor_type = sensor_type
        if self.series_id:
            dpg.set_value(self.series_id, [x_data, y_data])
            dpg.configure_item(self.series_id, label=f"{sensor_type} Data")
            dpg.fit_axis_data(self.x_axis_id)
            dpg.fit_axis_data(self.y_axis_id)


class UnitChannelPlot:
    def __init__(self, channel_type):
        self.channel_type = channel_type

    def build(self, channel_num, height):
        x_axis_tag = f"{self.channel_type}_ch{channel_num}_x_axis"
        y_axis_tag = f"{self.channel_type}_ch{channel_num}_y_axis"
        series_tag = f"{self.channel_type}_ch{channel_num}_series"
        plot_tag = f"{self.channel_type}_ch{channel_num}_plot"
        group_ch_plot_tag = f"{self.channel_type}_ch{channel_num}_group_ch_plot"
        max_y_axis_tag = f"{self.channel_type}_ch{channel_num}_max_y_axis"
        min_y_axis_tag = f"{self.channel_type}_ch{channel_num}_min_y_axis"

        with dpg.group(horizontal=True, tag=group_ch_plot_tag, height=height):
            # Left Panel: Clean borderless text controls
            with dpg.child_window(auto_resize_x=True, width=15, height=0, border=False, no_scrollbar=True):
                dpg.add_text(f"{channel_num}")

            # Right Panel: Plot Viewport Area
            with dpg.plot(height=0, width=-1, tag=plot_tag):
                
                dpg.add_plot_axis(dpg.mvXAxis, tag=x_axis_tag, no_tick_labels=True, no_tick_marks=False, no_gridlines=True)
                dpg.add_plot_axis(dpg.mvYAxis, tag=y_axis_tag, no_tick_labels=True, no_tick_marks=False)
                
                dpg.add_line_series([], [], parent=y_axis_tag, tag=series_tag)

                dpg.add_plot_annotation(label=f"{ 200}", default_value=(-25, 999999), 
                                        offset=(0, 0),  color=[0, 0, 0, 80],
                                        clamped=True, tag=max_y_axis_tag)
                
                dpg.add_plot_annotation(label=f"{-200}", default_value=(-25, -999999), 
                                        offset=(0, 0),  color=[0, 0, 0, 80],
                                        clamped=True, tag=min_y_axis_tag)

            dpg.bind_item_theme(plot_tag, "plot_theme")
            dpg.bind_item_theme(series_tag, f"color_{channel_num-1}")


class MarkerChannelPlot:
    def __init__(self, channel_type):
        self.channel_type = channel_type

    def build(self, channel_num, height):
        x_axis_tag = f"{self.channel_type}_ch{channel_num}_x_axis"
        y_axis_tag = f"{self.channel_type}_ch{channel_num}_y_axis"
        series_tag = f"{self.channel_type}_ch{channel_num}_series"
        plot_tag = f"{self.channel_type}_ch{channel_num}_plot"
        group_ch_plot_tag = f"{self.channel_type}_ch{channel_num}_group_ch_plot"

        with dpg.group(horizontal=True, tag=group_ch_plot_tag, height=height):
            with dpg.child_window(auto_resize_x=True, width=15, height=0,
                                  border=False, no_scrollbar=True):
                dpg.add_text(f"{channel_num}")

            with dpg.plot(height=0, width=-1, tag=plot_tag):
                dpg.add_plot_axis(dpg.mvXAxis, tag=x_axis_tag,
                                  no_tick_labels=True, no_tick_marks=False,
                                  no_gridlines=True)
                dpg.add_plot_axis(dpg.mvYAxis, tag=y_axis_tag,
                                  no_tick_labels=True, no_tick_marks=False)
                dpg.add_line_series([], [], parent=y_axis_tag, tag=series_tag)
                dpg.set_axis_limits(y_axis_tag, -1, 1)

            dpg.bind_item_theme(plot_tag, "plot_theme")
            dpg.bind_item_theme(series_tag, "color_0")


class UnitShadeChannelPlot:
    def __init__(self, channel_type):
        self.channel_type = channel_type

    def build(self, channel_num, height):
        x_axis_tag = f"{self.channel_type}_ch{channel_num}_x_axis"
        y_axis_tag = f"{self.channel_type}_ch{channel_num}_y_axis"
        series_tag = f"{self.channel_type}_ch{channel_num}_series"
        shade_tag = f"{self.channel_type}_ch{channel_num}_shade"
        plot_tag = f"{self.channel_type}_ch{channel_num}_plot"
        group_ch_plot_tag = f"{self.channel_type}_ch{channel_num}_group_ch_plot"
        max_y_axis_tag = f"{self.channel_type}_ch{channel_num}_max_y_axis"
        min_y_axis_tag = f"{self.channel_type}_ch{channel_num}_min_y_axis"

        with dpg.group(horizontal=True, tag=group_ch_plot_tag, height=height):
            # Left Panel: Clean borderless text controls
            with dpg.child_window(auto_resize_x=True, width=15, height=0, border=False, no_scrollbar=True):
                dpg.add_text(f"{channel_num}")

            # Right Panel: Plot Viewport Area
            with dpg.plot(height=0, width=-1, tag=plot_tag):
                
                dpg.add_plot_axis(dpg.mvXAxis, tag=x_axis_tag, no_tick_labels=True, no_tick_marks=False, no_gridlines=True)
                dpg.add_plot_axis(dpg.mvYAxis, tag=y_axis_tag, no_tick_labels=True, no_tick_marks=False)
                
                dpg.add_line_series([], [], parent=y_axis_tag, tag=series_tag)
                dpg.add_shade_series([], [], y2=[], parent=y_axis_tag, tag=shade_tag)

                dpg.add_plot_annotation(label=f"{ 200}", default_value=(-25, 999999), 
                                        offset=(0, 0),  color=[0, 0, 0, 80],
                                        clamped=True, tag=max_y_axis_tag)
                
                dpg.add_plot_annotation(label=f"{-200}", default_value=(-25, -999999), 
                                        offset=(0, 0),  color=[0, 0, 0, 80],
                                        clamped=True, tag=min_y_axis_tag)

            dpg.bind_item_theme(plot_tag, "plot_theme")
            dpg.bind_item_theme(series_tag, f"color_{channel_num-1}")
            dpg.bind_item_theme(shade_tag, f"color_{channel_num-1}")



class EnEEGChannel:
    def __init__(self, channel_num):
        self.channel_num = channel_num
        self.tag = f"en_eeg_ch{channel_num}"
        self.group_ch_plot_tag = f"eeg_ch{channel_num}_group_ch_plot"

    def build(self):
        if self.channel_num < 10:
            dpg.add_checkbox(label=f' {self.channel_num}', default_value=True, 
                            callback=self.en_eeg_ch_callback, tag=self.tag)
        else:
            dpg.add_checkbox(label=f'{self.channel_num}', default_value=True, 
                            callback=self.en_eeg_ch_callback, tag=self.tag)
    
    def en_eeg_ch_callback(self):
        en_ch = dpg.get_value(self.tag)
        dpg.configure_item(self.group_ch_plot_tag, show=en_ch)


class AxisOnlyPlot:
    def __init__(self, channel_type):
        self.channel_type = channel_type
        self.plot_tag = f"{channel_type}_static_plot"
        self.x_axis_tag = f"{channel_type}_static_x_axis"
        self.y_axis_tag = f"{channel_type}_static_y_axis"
    
    def build(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=15, height=40, border=False, no_scrollbar=True):
                pass

            with dpg.plot(height=40, width=-1, no_title=True, tag=self.plot_tag):
                # X-Axis continuously streaming forward
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (seconds)", tag=self.x_axis_tag, no_tick_marks=True)
                dpg.add_plot_axis(dpg.mvYAxis, tag=self.y_axis_tag, no_tick_marks=True, no_tick_labels=True)
                dpg.set_axis_limits(self.y_axis_tag , -150.0, 150.0)
                
                # Bind transparency layouts to keep workspace completely clean
                dpg.bind_item_theme(self.plot_tag, "transparent_plot_theme")


class SyncedSlider:
    def __init__(self, tag_name, label, default_value=10, min_val=0, max_val=40, width=350, parent=None):
        self.tag_name = tag_name
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.default_value = default_value
        self.width = width
        self.parent = parent
        
        # Register the shared value using your explicit name
        with dpg.value_registry():
            # Check if the tag already exists to prevent crashes
            if not dpg.does_alias_exist(self.tag_name):
                dpg.add_int_value(default_value=self.default_value, tag=self.tag_name)

    def build(self):
        container_kwargs = {"parent": self.parent} if self.parent else {}
        
        container_kwargs["tag"] = f"{self.tag_name}_container"
        with dpg.group(**container_kwargs):
            dpg.add_spacer(height=10)
            
            # Top Row: Table handles perfect flush alignment
            with dpg.table(header_row=False, width=self.width, 
                           borders_innerV=False, borders_outerV=False, 
                           borders_innerH=False, borders_outerH=False):
                # The first column stretches, pushing the second column to the right
                dpg.add_table_column(width_stretch=True)
                # The second column fits exactly to the size of the input box
                dpg.add_table_column(width_fixed=True)
                
                with dpg.table_row():
                    dpg.add_text(self.label)
                    # Width adjusted slightly so digits aren't cut off
                    dpg.add_input_int(width=40, step=0, source=self.tag_name) 
            
            # Middle Row: The Slider
            dpg.add_slider_int(
                width=self.width, 
                min_value=self.min_val, 
                max_value=self.max_val, 
                format="", 
                source=self.tag_name
            )
            
            # Bottom Row: Table handles left/right alignment automatically
            with dpg.table(header_row=False, width=self.width, 
                           borders_innerV=False, borders_outerV=False, 
                           borders_innerH=False, borders_outerH=False):
                dpg.add_table_column(width_stretch=True)
                dpg.add_table_column(width_fixed=True)
                
                with dpg.table_row():
                    dpg.add_text(str(self.min_val))
                    dpg.add_text(str(self.max_val))

    def get_value(self):
        """Retrieve the value using your explicit tag."""
        return dpg.get_value(self.tag_name)

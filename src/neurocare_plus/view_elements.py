import math
import dearpygui.dearpygui as dpg


class DeviceBlock:
    """A self-contained hardware control component."""
    def __init__(self, device_name, btn_tag):
        self.device_name = device_name
        self.btn_tag = btn_tag
        self.status_tag = btn_tag + "_status"
        self.indicator_tag = btn_tag + "_indicator"

    def build(self):
        with dpg.group():
            # Add text and button
            dpg.add_text(self.device_name, color=[255, 255, 255])
            dpg.add_button(label="Start Device", width=-1, tag=self.btn_tag)
            
            # Status indicator placed cleanly beneath the button
            with dpg.group(horizontal=True):
                # Drawlist height set to 20 to cleanly accommodate center tracking at Y=10
                with dpg.drawlist(width=16, height=20):
                    dpg.draw_circle(
                        center=[8, 10], radius=5, 
                        color=[128, 128, 128, 255], fill=[128, 128, 128, 255], 
                        tag=self.indicator_tag
                    )
                dpg.add_text("Disconnected", color=[160, 160, 160], tag=self.status_tag)
                
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)


class ComboDisplayWidget:
    def __init__(self, combo_item_list=[], widget_list=[], display_tag='', height=0, default_value: str = ''):
        self.combo_item_list = combo_item_list
        self.widget_list = widget_list
        self.display_tag = display_tag
        self.combo2widget_dict = self._make_combo2widget_map(combo_item_list, widget_list)
        self.widget2combo_dict = self._make_widget2combo_map(widget_list, combo_item_list)
        self.height = height
        self.default_value = default_value

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

        if (dpg.does_item_exist("monitor_sec_display") 
            and dpg.does_item_exist("eeg_plots_parent")):
            dpg.split_frame()
            window_resize_handler(None, None, None)

    def build(self):
        with dpg.child_window(tag=self.display_tag, border=False, height=self.height):
            dpg.add_combo(items=self.combo_item_list, tag=f"combo_{self.display_tag}",
                          callback=self.dropdown_callback, user_data=self.display_tag, 
                          default_value=self.default_value, width=200)
        if self.default_value:
            self.dropdown_callback(f"combo_{self.display_tag}", self.default_value, self.display_tag)


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


class EEGPlot:
    def __init__(self, tag, default_sensor="EEG", height=-1, parent=0):
        self.tag = tag
        self.sensor_type = default_sensor
        self.height = height
        self.parent = parent

        self.eeg_ch_plot = EEGChannelPlot()
        self.en_eeg_ch= {i: EnEEGChannel(channel_num=i) for i in range(1,17)}

        self.combo2vertscale_dict = {
            "50 uV": 50,
            "100 uV": 100,
            "200 uV": 200,
            "400 uV": 400,
            "1000 uV": 1000,
            "10000 uV": 10000,
            "Auto": None
        }
        
        self.combo2twindow_dict = {
            "1 sec": 1,
            "3 sec": 3,
            "5 sec": 5,
            "10 sec": 10,
            "20 sec": 20,
        }

        self.build()

    def build(self):
        with dpg.child_window(tag=self.tag, border=True, height=self.height, width=-1, parent=self.parent):

            # Collapsing Header
            with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit, tag="eeg_options_table"):
                dpg.add_table_column(width_stretch=True) # Full width for the header
                dpg.add_table_column(width_fixed=True)   # Tight fit for the button
                dpg.add_table_column(width_fixed=True)
                
                with dpg.table_row():
                    # 1st Column
                    with dpg.collapsing_header(indent=4, label="Channel Options", tag='header_channels'):
                        with dpg.group(horizontal=True):
                            for i in range(1,9):
                                self.en_eeg_ch[i].build()
                        with dpg.group(horizontal=True):
                            for i in range(9,17):
                                self.en_eeg_ch[i].build()
                        
                    # 2nd Column
                    with dpg.group(horizontal=True, indent=4):
                        dpg.add_combo(items=["Auto","50 uV","100 uV","200 uV","400 uV","1000 uV","10000 uV"],
                                      default_value="200 uV", tag="combo_vert_scale", width=80,
                                      callback=self.vert_scale_callback)
                    
                    # 3rd Column
                    dpg.add_combo(items=["1 sec","3 sec","5 sec","10 sec","20 sec"], 
                                  default_value="5 sec", tag="combo_time_window", width=80,
                                  callback=self.time_window_callback)

            # Spacer
            dpg.add_spacer(height=1)

            # Plotting All 8 Channels
            with dpg.child_window(border=False, tag="eeg_plots_parent", height=-45):
                for i in range(1,9):
                    self.eeg_ch_plot.build(channel_num=i,height=100)

            # Plotting just the Axis
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=35)

                with dpg.plot(height=40, width=-1, no_title=True, tag="timeline_plot_widget"):
                    # X-Axis continuously streaming forward
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (seconds)", tag="global_x_axis", no_tick_marks=True)
                    dpg.add_plot_axis(dpg.mvYAxis, tag="global_y_axis_spacer", no_tick_marks=True, no_tick_labels=True)
                    dpg.set_axis_limits("global_y_axis_spacer", -150.0, 150.0)
                    
                    # Bind transparency layouts to keep workspace completely clean
                    dpg.bind_item_theme("timeline_plot_widget", "transparent_plot_theme")

            # Default Value Callback
            self.vert_scale_callback(None, "200 uV", None)
            self.time_window_callback(None, "5 sec", None)

    def vert_scale_callback(self, sender, app_data, user_data):
        VERT_SCALE = self.combo2vertscale_dict[app_data]
        if VERT_SCALE:
            for channel_num in range(1,9):
                dpg.set_axis_limits(f"eeg_ch{channel_num}_y_axis",-VERT_SCALE,VERT_SCALE)

    def time_window_callback(self, sender, app_data, user_data):
        WINDOW_TIME = self.combo2twindow_dict[app_data]
        for channel_num in range(1,9):
            dpg.set_axis_limits(f"eeg_ch{channel_num}_x_axis", -WINDOW_TIME  , 0)
        dpg.set_axis_limits("global_x_axis", -WINDOW_TIME, 0)


class EEGChannelPlot:
    def __init__(self):
        pass

    def build(self, channel_num, height):
        x_axis_tag = f"eeg_ch{channel_num}_x_axis"
        y_axis_tag = f"eeg_ch{channel_num}_y_axis"
        series_tag = f"eeg_ch{channel_num}_series"
        plot_tag = f"eeg_ch{channel_num}_plot"
        group_ch_plot_tag = f"eeg_ch{channel_num}_group_ch_plot"

        with dpg.group(horizontal=True, tag=group_ch_plot_tag):
            # Left Panel: Clean borderless text controls
            with dpg.child_window(auto_resize_x=True, height=height, border=False, no_scrollbar=True):
                dpg.add_text(f"{channel_num}")

            # Right Panel: Plot Viewport Area
            with dpg.plot(height=100, width=-1, tag=plot_tag):
                
                dpg.add_plot_axis(dpg.mvXAxis, tag=x_axis_tag, no_tick_labels=True)
                dpg.add_plot_axis(dpg.mvYAxis, tag=y_axis_tag)
                
                dpg.add_line_series([], [], parent=y_axis_tag, tag=series_tag)

            dpg.bind_item_theme(plot_tag, "plot_theme")


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
        window_resize_handler("None", "None", 53)


def window_resize_handler(sender, app_data, user_data):
    print("[Resize] Window Callback")

    #----- Monitor Tab Secondary Display -----#
    parent_height = dpg.get_item_rect_size("monitor_sec_display")[1]
    
    # Subtracting height of spacers to prevent scroll bar from appearing.
    available_height = parent_height - 26
    
    # Ensure height doesn't drop below a minimum threshold
    if available_height > 20:
        half_height = available_height // 2
        
        # Apply the new 50% heights to the exact string tags
        dpg.configure_item("alpha_display", height=half_height)
        dpg.configure_item("beta_display", height=half_height)

    #----- Monitor Tab Secondary Display -----#
    eeg_plot_parent_height = dpg.get_item_rect_size("eeg_plots_parent")[1]

    en_spacer = 0
    if user_data is not None:
        en_spacer = user_data

    # Subtracting height of spacers to prevent scroll bar from appearing.
    available_height = eeg_plot_parent_height - 28 + en_spacer

    count = 0
    for channel_num in range(1,9):
        if dpg.get_value(f"en_eeg_ch{channel_num}"):
            count += 1

    if available_height > 20:
        portion_height = available_height // count
        
        for channel_num in range(1,9):
            if dpg.get_value(f"en_eeg_ch{channel_num}"):
                dpg.configure_item(f"eeg_ch{channel_num}_group_ch_plot", height=portion_height)

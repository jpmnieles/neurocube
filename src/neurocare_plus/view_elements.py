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
    def __init__(self, combo_item_list=[], widget_list=[], display_tag=''):
        self.combo_item_list = combo_item_list
        self.widget_list = widget_list
        self.display_tag = display_tag
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

        try:
            dpg.split_frame()
            window_resize_handler(None, None, None)
        except:
            pass
                

    def build(self, default_value=''):
        dpg.add_combo(items=self.combo_item_list, tag=f"combo_{self.display_tag}",
                        callback=self.dropdown_callback, user_data=self.display_tag, 
                        default_value=default_value, width=200)
        if default_value:
            self.dropdown_callback(f"combo_{self.display_tag}", default_value, self.display_tag)


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

        with dpg.group(horizontal=True, tag=group_ch_plot_tag, height=height):
            # Left Panel: Clean borderless text controls
            with dpg.child_window(auto_resize_x=True, height=0, border=False, no_scrollbar=True):
                dpg.add_text(f"{channel_num}")

            # Right Panel: Plot Viewport Area
            with dpg.plot(height=0, width=-1, tag=plot_tag):
                
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
        window_resize_handler(None, None, None)


def window_resize_handler(sender, app_data, user_data):
    print("[Resize] Window Callback")

    #----- Monitor Tab Secondary Display (For Alpha and Beta Displays) -----#
    if dpg.get_item_configuration("monitor_sec_display")['show']:
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
    eeg_collapsing_header_height = -19

    if dpg.get_item_configuration("eeg_plots_parent")['show']:
        if user_data and ("EEG_Collapsing_Header" in user_data):  # Hardcoded Option because State is Delayed
            if user_data["EEG_Collapsing_Header"]:
                eeg_collapsing_header_height = -67
            else:
                eeg_collapsing_header_height = 21

    # Subtracting height of spacers to prevent scroll bar from appearing.
    available_height = eeg_plot_parent_height + eeg_collapsing_header_height - 11

    visible_ch = [i for i in range(1, 9) if dpg.get_value(f"en_eeg_ch{i}")]

    if available_height > 20:
        portion_height = available_height // len(visible_ch)
        
        for channel_num in visible_ch:
            dpg.configure_item(f"eeg_ch{channel_num}_group_ch_plot", height=portion_height)

import math
import dearpygui.dearpygui as dpg


class DeviceBlock:
    """A self-contained hardware control component."""
    def __init__(self, device_name):
        self.device_name = device_name
        self.is_connected = False
        
        self.status_text_id = None
        self.indicator_id = None
        self.button_id = None

    def build(self):
        with dpg.group():
            dpg.add_text(self.device_name, color=[255, 255, 255])
            
            self.button_id = dpg.add_button(
                label="Start Device", 
                width=120, 
                callback=self._on_toggle_click
            )
            
            # Status indicator placed cleanly beneath the button
            with dpg.group(horizontal=True):
                # Drawlist height set to 20 to cleanly accommodate center tracking at Y=10
                with dpg.drawlist(width=16, height=20):
                    self.indicator_id = dpg.draw_circle(
                        center=[8, 10], radius=5, 
                        color=[128, 128, 128, 255], fill=[128, 128, 128, 255]
                    )
                self.status_text_id = dpg.add_text("Disconnected", color=[160, 160, 160])
                
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)

    def _on_toggle_click(self, sender, app_data):
        self.is_connected = not self.is_connected
        
        if self.is_connected:
            dpg.set_value(self.status_text_id, "Connected")
            dpg.configure_item(self.indicator_id, color=[0, 255, 0, 255], fill=[0, 255, 0, 255])
            dpg.configure_item(self.button_id, label="Stop Device")
        else:
            dpg.set_value(self.status_text_id, "Disconnected")
            dpg.configure_item(self.indicator_id, color=[128, 128, 128, 255], fill=[128, 128, 128, 255])
            dpg.configure_item(self.button_id, label="Start Device")


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

        self.build()

    def build(self):
        with dpg.child_window(tag=self.tag, border=True, height=self.height, width=-1, parent=self.parent):
            with dpg.plot(height=-1, width=-1):
                
                # 2. Add the reference X-Axis (Child of the plot)
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (Seconds)", tag="x_axis")
                
                # 3. Add the reference Y-Axis (Child of the plot)
                # Note: We capture its returned ID or define a tag to assign the line series parent
                dpg.add_plot_axis(dpg.mvYAxis, label="Amplitude (Voltage)", tag="y_axis")
                
                # 4. Push data series strictly as a child of the targeted Y-Axis
                dpg.add_line_series([], [], label="Sensor Alpha", parent="y_axis", tag="Plot_Series_Tag")
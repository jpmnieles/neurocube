import view_elements
import dearpygui.dearpygui as dpg


class MainView:
    def __init__(self):
        # DPG Initialization
        dpg.create_context()
        
        ### Themes ###
        with dpg.theme(tag="table_no_pad_theme"):
            with dpg.theme_component(dpg.mvTable):
                # Change the cell padding to [X-axis padding, Y-axis padding]
                dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 5, 0, category=dpg.mvThemeCat_Core)

        with dpg.theme(tag="green_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, [40, 150, 80, 255])         # Idle Green
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [50, 180, 100, 255]) # Hover Green
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [30, 120, 60, 255])   # Click Green

        with dpg.theme(tag="red_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, [180, 50, 50, 255])         # Idle Red
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [210, 70, 70, 255])  # Hover Red
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [140, 30, 30, 255])   # Click Red
        
        # Setup Hidden Staging Window
        self._build_hidden_staging_window()

        # Initialize Widgets
        self.primary_plot = view_elements.EEGPlot("EEG_widget", "EEG",   # Any Widget Plots
                                                      height=0, parent="hidden_stage")  
        self.alpha_plot = view_elements.DynamicPlot("PPG_widget", "PPG", 
                                                    height=0, parent="hidden_stage")  # TODO: Change to dynamic 50% of the height
        self.beta_plot = view_elements.DynamicPlot("IMU_widget", "IMU", 
                                                   height=0, parent="hidden_stage")
        
        # View Components
        self.menu_bar = MenuBar()
        self.device_panel = DevicePanel()
        self.logger_panel = LoggerPanel()
        self.monitor_tab = MonitorTab()
        self.eeg_tab = EEGTab()
        self.smartwatch_tab = SmartwatchTab()

    def _build_hidden_staging_window(self):
        with dpg.window(tag="hidden_stage", no_move=True, no_resize=True, show=False): 
            pass
    
    def build(self):
        # Main Window
        with dpg.window(tag="Main_App_Window", no_title_bar=True, no_resize=True, no_move=True, no_scrollbar=True):
            
            # Menu Bar
            self.menu_bar.build()
            
            # Main Window Place Holder
            with dpg.group(horizontal=True, height=-70):

                # Device Panel
                self.device_panel.build()
                
                # Multipanel
                with dpg.child_window(label="Multipanel", border=False, height=0):
                    with dpg.tab_bar():
                        self.monitor_tab.build()
                        self.eeg_tab.build()
                        self.smartwatch_tab.build()
            
            # Logger Panel
            self.logger_panel.build()

    def setup(self):

        # DPG and OS Viewport Setup
        dpg.create_viewport(title='Neuro\u00b3 GUI', width=1920, height=1080)
        dpg.setup_dearpygui()
        dpg.set_primary_window("Main_App_Window", True)
        dpg.set_viewport_resize_callback(self.window_resize_handler)
        dpg.show_viewport()

    def teardown(self):
        dpg.destroy_context()
    
    def is_gui_running(self):
        return dpg.is_dearpygui_running()
    
    def render_gui_frame(self):
        return dpg.render_dearpygui_frame()
    
    def window_resize_handler(self):
        print("[Resize] Window Callback")

        # Monitor Tab Secondary Display
        parent_height = dpg.get_item_rect_size("monitor_sec_display")[1]
        
        # Subtracting height of spacers to prevent scroll bar from appearing.
        available_height = parent_height - 26
        
        # Ensure height doesn't drop below a minimum threshold
        if available_height > 20:
            half_height = available_height // 2
            
            # Apply the new 50% heights to the exact string tags
            dpg.configure_item("alpha_display", height=half_height)
            dpg.configure_item("beta_display", height=half_height)

class MenuBar:
    
    def build(self):
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Save Configuration")
                dpg.add_menu_item(label="Exit")
            with dpg.menu(label="Devices"):
                dpg.add_menu_item(label="Refresh Ports")


class DevicePanel:
    def __init__(self):
        self.devices = [
            view_elements.DeviceBlock("OpenBCI EEG", "btn_eeg_device_connect"),
            view_elements.DeviceBlock("Emotibit", "btn_emotibit_device_connect"),
            view_elements.DeviceBlock("PBM Module", "btn_pbm_device_connect")
        ]

    def build(self):
        with dpg.child_window(label="Device Rack Layout", width=150, height=0):  # Device Panel
            dpg.add_text("DEVICES", color=[150, 150, 255])
            dpg.add_separator()
            dpg.add_spacer(height=5)
            
            # Individual HW Devices Connect/Disconnect
            for device in self.devices:
                device.build()

            # Placeholder for the space
            with dpg.child_window(height=-50, border=False):
                pass

            # Start and Stop Stream
            with dpg.group(horizontal=True, height=45):
                dpg.add_button(label="Start\nStream", tag="start_stream_btn", width=62.5)
                dpg.add_button(label="Stop\nStream", tag="stop_stream_btn", width=-1)

            dpg.bind_item_theme(item="start_stream_btn", theme="green_btn_theme")
            dpg.bind_item_theme(item="stop_stream_btn", theme="red_btn_theme")


class LoggerPanel:

    def build(self):
        dpg.add_text("LOGGER", color=[150, 150, 255])
        dpg.add_separator()
        with dpg.child_window(height=0, border=False, no_scrollbar=False, tag="status_window", label="Console Log", tracked=True):
            dpg.add_text("System active.\n", tag="log_stream", color=[200, 200, 200])


class MonitorTab:

    def __init__(self):
        
        self.primary_select = view_elements.ComboDisplayWidget(
            combo_item_list=['EEG','PPG','IMU'],
            widget_list=['EEG_widget','PPG_widget','IMU_widget'],
            display_tag='primary_display',
            default_value='EEG'
        )
        self.alpha_select = view_elements.ComboDisplayWidget(
            combo_item_list=['EEG','PPG','IMU'],
            widget_list=['EEG_widget','PPG_widget','IMU_widget'],
            display_tag='alpha_display',
            height=420
        )
        self.beta_select = view_elements.ComboDisplayWidget(
            combo_item_list=['EEG','PPG','IMU'],
            widget_list=['EEG_widget','PPG_widget','IMU_widget'],
            display_tag='beta_display'
        )

    def build(self):
        # Referenced to Main View Tab
        with dpg.tab(label="Monitor"):
            # Adding Explicit Top Spacer
            dpg.add_spacer(height=2)

            # DPG Table for Modular Display Configuration
            with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp, 
                           resizable=True, scrollX=True, scrollY=True, height=0, tag='monitor_table'):
                
                # Column Width: 60% Primary Display, 40% Secondary Display
                dpg.add_table_column(init_width_or_weight=0.60)
                dpg.add_table_column(init_width_or_weight=0.40)
                
                # Insert Table Row
                with dpg.table_row():
                    
                    # COLUMN 1: Primary Display
                    with dpg.child_window(border=False, height=0):

                        ## Display 1
                        self.primary_select.build()
                    
                    # COLUMN 2: Secondary Displays
                    with dpg.child_window(border=False, height=0, no_scrollbar=True,
                                          tag="monitor_sec_display"):
                        
                        ## Display 2A
                        self.alpha_select.build()
                        
                        ## Separator
                        dpg.add_spacer(height=5)
                        dpg.add_separator()
                        dpg.add_spacer(height=5)
                        
                        ## Display 2B
                        self.beta_select.build()

            # Bind the theme
            dpg.bind_item_theme("monitor_table", "table_no_pad_theme")


class EEGTab:

    def build(self):
        with dpg.tab(label="EEG Overview"):
            with dpg.child_window(label="Test", height=0):
                dpg.add_text("Dedicated EEG Signal Processor Panel", color=[150, 255, 150])


class SmartwatchTab:

    def build(self):
        with dpg.tab(label="Smartwatch"):
            with dpg.child_window(label="Test", height=0):
                dpg.add_text("Biometric Stream Feed Configurations", color=[255, 150, 150])

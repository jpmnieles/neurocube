import view_elements
import dearpygui.dearpygui as dpg
from datetime import datetime

from widgets import WidgetManager


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

        with dpg.theme(tag="transparent_plot_theme"):
            with dpg.theme_component(dpg.mvPlot):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 1, 1, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvPlotStyleVar_PlotPadding, 0, 0, category=dpg.mvThemeCat_Plots)
                # dpg.add_theme_style(dpg.mvPlotStyleVar_MinorAlpha, 0.0, category=dpg.mvThemeCat_Plots)
                # dpg.add_theme_style(dpg.mvPlotStyleVar_MajorGridSize, 1.0, 1.0, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_FrameBg, [0, 0, 0, 0], category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_PlotBg, [0, 0, 0, 0], category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_PlotBorder, [0, 0, 0, 0], category=dpg.mvThemeCat_Plots)

        with dpg.theme(tag="plot_theme"):
            with dpg.theme_component(dpg.mvPlot):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 1, 1, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvPlotStyleVar_PlotPadding, 0, 0, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_MinorAlpha, 0.0, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_MajorGridSize, 1.0, 1.0, category=dpg.mvThemeCat_Plots)

        ### Colors  ###
        color_pool = [
                [255, 100, 100, 255], # 0. Bright Red
                [100, 200, 255, 255], # 1. Light Blue
                [100, 255, 100, 255], # 2. Bright Green
                [255, 255, 100, 255], # 3. Yellow
                [255, 100, 255, 255], # 4. Magenta
                [100, 255, 255, 255], # 5. Cyan
                [255, 180, 100, 255], # 6. Orange
                [200, 150, 255, 255], # 7. Light Purple
                [150, 100, 50, 255],  # 8. Brown
                [50, 150, 100, 255],  # 9. Dark Sea Green
                [100, 50, 150, 255],  # 10. Deep Purple
                [200, 100, 150, 255], # 11. Dusty Rose
                [150, 200, 100, 255], # 12. Olive/Lime
                [100, 150, 200, 255], # 13. Steel Blue
                [255, 150, 150, 255], # 14. Light Salmon
                [150, 255, 150, 255], # 15. Pale Green
                [150, 150, 255, 255], # 16. Periwinkle
                [255, 200, 150, 255], # 17. Peach
                [200, 255, 150, 255], # 18. Yellow-Green
                [150, 200, 255, 255], # 19. Sky Blue
                [255, 100, 150, 255], # 20. Hot Pink
                [150, 255, 200, 255], # 21. Aquamarine
                [200, 150, 100, 255], # 22. Tan/Bronze
                [255, 220, 200, 255], # 23. Apricot
                [200, 200, 100, 255]  # 24. Khaki/Gold
            ]
        shade_pool = []
        for i in range(len(color_pool)):
            shade_pool.append(color_pool[i][:3]+[100])

        for i in range(25):
            with dpg.theme(tag=f"color_{i}"):
                with dpg.theme_component(dpg.mvLineSeries):
                    dpg.add_theme_color(dpg.mvPlotCol_Line, color_pool[i], category=dpg.mvThemeCat_Plots)
                with dpg.theme_component(dpg.mvShadeSeries):
                    dpg.add_theme_color(dpg.mvPlotCol_Line, shade_pool[i], category=dpg.mvThemeCat_Plots)
                    dpg.add_theme_color(dpg.mvPlotCol_Fill, shade_pool[i], category=dpg.mvThemeCat_Plots)

        ### Font Sizes###
        with dpg.font_registry():
            font_path = "resource/ProggyClean.ttf"  
            for size in range(1, 201):
                dpg.add_font(font_path, size, tag=f"dynamic_font_{size}")
            
        # Setup Widgets
        self.widgets = WidgetManager()
        
        # View Components
        self.menu_bar = MenuBar()
        self.device_panel = DevicePanel()
        self.logger_panel = LoggerPanel()
        self.monitor_tab = MonitorTab()
        self.eeg_tab = EEGTab()
        self.smartwatch_tab = SmartwatchTab()
        self.medicalforms_tab = MedicalFormsTab()

        dpg.show_metrics()
    
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
                        self.medicalforms_tab.build()
            
            # Logger Panel
            self.logger_panel.build()

    def setup(self):

        # DPG and OS Viewport Setup
        dpg.create_viewport(title='Neuro\u00b3 GUI', width=1920, height=1080)
        dpg.setup_dearpygui()
        dpg.set_primary_window("Main_App_Window", True)
        dpg.show_viewport()

    def teardown(self):
        dpg.destroy_context()
    
    def is_gui_running(self):
        return dpg.is_dearpygui_running()
    
    def render_gui_frame(self):
        return dpg.render_dearpygui_frame()


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
            combo_item_list=['EEG','PPG','IMU','Temperature','GSR/EDA'],
            widget_list=['EEG_widget','PPG_widget','IMU_widget','Temp_widget','GSR_widget'],
            display_tag='primary_display'
        )
        self.alpha_select = view_elements.ComboDisplayWidget(
            combo_item_list=['EEG','PPG','IMU','Temperature','GSR/EDA'],
            widget_list=['EEG_widget','PPG_widget','IMU_widget','Temp_widget','GSR_widget'],
            display_tag='alpha_display'
        )
        self.beta_select = view_elements.ComboDisplayWidget(
            combo_item_list=['EEG','PPG','IMU','Temperature','GSR/EDA'],
            widget_list=['EEG_widget','PPG_widget','IMU_widget','Temp_widget','GSR_widget'],
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
                    with dpg.child_window(border=False, height=0, tag="primary_display"):

                        ## Display 1
                        self.primary_select.build('EEG')
                    
                    # COLUMN 2: Secondary Displays
                    with dpg.child_window(border=False, height=0, no_scrollbar=True,
                                          tag="monitor_sec_display"):
                        
                        ## Display 2A
                        with dpg.child_window(border=False, height=420, tag="alpha_display"):
                            self.alpha_select.build('PPG')
                        
                        ## Separator
                        dpg.add_spacer(height=5)
                        dpg.add_separator()
                        dpg.add_spacer(height=5)
                        
                        ## Display 2B
                        with dpg.child_window(border=False, height=0, tag="beta_display"):
                            self.beta_select.build('GSR/EDA')

            # Bind the theme
            dpg.bind_item_theme("monitor_table", "table_no_pad_theme")


class MedicalFormsTab:
    def __init__(self):
        self.tag = "medform"

        self._get_date_today()

    def build(self):
        with dpg.tab(label="Medical Forms"):
            with dpg.child_window(height=0):
                #----- New, Edit, Save Buttons -----
                with dpg.group(horizontal=True):
                    dpg.add_button(label="New", width=65, height=30, tag=f"{self.tag}_new_btn")
                    dpg.add_button(label="Edit", width=65, height=30, tag=f"{self.tag}_edit_btn")
                    dpg.add_button(label="Save", width=65, height=30, tag=f"{self.tag}_save_btn")

                dpg.add_spacer(height=10)

                #----- Search Bar -----
                with dpg.group(horizontal=True):
                    dpg.add_input_text(hint="Participant Code", width=300)
                    dpg.add_button(label="Search", width=60, tag=f"{self.tag}_search_btn")

                #----- Spacers for Search Bar & Forms -----
                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=2)

                # ----- Start of Medical Forms -----
                with dpg.child_window(border=False):  
                    # First Line     
                    with dpg.group(horizontal=True):
                        dpg.add_text("Participant Code: ")
                        dpg.add_input_text(width=80)

                        dpg.add_spacer(width=10)

                        dpg.add_text("Date of Enrollment: ")
                        dpg.add_input_text(
                            tag=f"{self.tag}_date_input_field",
                            default_value=self.formatted_today_str,
                            readonly=True, width=80)

                    # Popup for Date    
                    with dpg.popup(parent=f"{self.tag}_date_input_field", 
                                    mousebutton=dpg.mvMouseButton_Left,
                                    tag=f"{self.tag}_date_popup"):
                        
                        dpg.add_date_picker(level=dpg.mvDatePickerLevel_Day,
                                            default_value=self.today_dict,
                                            callback=self.date_picker_callback)
                    dpg.set_item_pos(f"{self.tag}_date_popup", [562, 141])

                    # Study Arm
                    with dpg.group(horizontal=True):
                        dpg.add_text("Study Arm: ")
                        dpg.add_spacer(width=10)

                        dpg.add_checkbox(label="PBM Only")
                        dpg.add_spacer(width=10)

                        dpg.add_checkbox(label="PBM + Music Therapy")
                        dpg.add_spacer(width=10)

                        dpg.add_checkbox(label="PBM + Baduanjin")
                        dpg.add_spacer(width=10)

                        dpg.add_checkbox(label="Control")

                    dpg.add_spacer(height=5)

                    # SECTION A: SOCIODEMOGRAPHIC INFORMATION
                    with dpg.collapsing_header(label="SECTION A: SOCIODEMOGRAPHIC INFORMATION", 
                                               closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Data Item")
                            dpg.add_table_column(label="Response")

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row():
                                dpg.add_text("Age")
                                dpg.add_input_text(width=-1)

                            ## Row 2
                            with dpg.table_row():
                                dpg.add_text("Sex")
                                dpg.add_input_text(width=-1)

                            ## Row 3
                            with dpg.table_row():
                                dpg.add_text("Civil Status")
                                dpg.add_input_text(width=-1)

                            ## Row 4
                            with dpg.table_row():
                                dpg.add_text("Educational Attainment")
                                dpg.add_input_text(width=-1)

                            ## Row 5
                            with dpg.table_row():
                                dpg.add_text("Occupation")
                                dpg.add_input_text(width=-1)

                            ## Row 6
                            with dpg.table_row():
                                dpg.add_text("Living Arrangement")
                                dpg.add_input_text(width=-1)

                            ## Row 7
                            with dpg.table_row():
                                dpg.add_text("Primary Caregive (Name/Relationship)")
                                dpg.add_input_text(width=-1)

                            ## Row 8
                            with dpg.table_row():
                                dpg.add_text("Mobile Number of Caregiver")
                                dpg.add_input_text(width=-1)

                    dpg.add_spacer(height=15)

                    # SECTION B: CLINICAL HISTORY AND ELIGIBILITY
                    with dpg.collapsing_header(label="SECTION B: CLINICAL HISTORY AND ELIGIBILITY", 
                                            closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Item")
                            dpg.add_table_column(label="Yes / No / N/A")
                            dpg.add_table_column(label="Remarks")

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row(height=10):
                                dpg.add_text("Diagnosed with MCI or early-stage dementia?")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 2
                            with dpg.table_row(height=10):
                                dpg.add_text("History of stroke/TBI/epilepsy")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 3
                            with dpg.table_row(height=10):
                                dpg.add_text("Visual or auditory impairment")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 4
                            with dpg.table_row(height=10):
                                dpg.add_text("Using pacemaker or implanted devices")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 5
                            with dpg.table_row(height=10):
                                dpg.add_text("Taking psychoactive  medications")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                    dpg.add_spacer(height=15)

                    # SECTION C: INTERVENTION MONITORING (Per Session)
                    with dpg.collapsing_header(label="SECTION C: INTERVENTION MONITORING (Per Session)", 
                                            closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Session No.")
                            dpg.add_table_column(label="Date")
                            dpg.add_table_column(label="Intervention\nCompleted")
                            dpg.add_table_column(label="Notes on \nBehavior / Reaction")
                            dpg.add_table_column(label="Adverse Event (Y/N)")
                            dpg.add_table_column(label="Remarks")

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row(height=10):
                                dpg.add_text("1")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 2
                            with dpg.table_row(height=10):
                                dpg.add_text("2")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 3
                            with dpg.table_row(height=10):
                                dpg.add_text("3")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 4
                            with dpg.table_row(height=10):
                                dpg.add_text("4")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 5
                            with dpg.table_row(height=10):
                                dpg.add_text("5")
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)

                    dpg.add_spacer(height=15)
                    
                    # SECTION D: POST-INTERVENTION ASSESSMENTS
                    with dpg.collapsing_header(label="SECTION D: POST-INTERVENTION ASSESSMENTS", 
                                            closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Assessmen Tool")
                            dpg.add_table_column(label="Raw Score")
                            dpg.add_table_column(label="Percentile / Interpretation")

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row(height=10):
                                dpg.add_text("MMSE")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                            ## Row 2
                            with dpg.table_row(height=10):
                                dpg.add_text("MoCA")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                            ## Row 3
                            with dpg.table_row(height=10):
                                dpg.add_text("GDS")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                            ## Row 4
                            with dpg.table_row(height=10):
                                dpg.add_text("ADL Score")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                            ## Row 5
                            with dpg.table_row(height=10):
                                dpg.add_text("NPI-Q")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                            ## Row 6
                            with dpg.table_row(height=10):
                                dpg.add_text("EEG Changes (Band Power, Coherence, etc.)")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                            ## Row 7
                            with dpg.table_row(height=10):
                                dpg.add_text("ERP")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                            ## Row 8
                            with dpg.table_row(height=10):
                                dpg.add_text("HRV")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                            ## Row 9
                            with dpg.table_row(height=10):
                                dpg.add_text("Skin Temperature (mean °C)")
                                dpg.add_input_text(width=-1)
                                dpg.add_input_text(width=-1)

                    dpg.add_spacer(height=15)
                                    
                    # SECTION E: QUALITATIVE FEEDBACK (Participant and/or Caregiver)
                    with dpg.collapsing_header(label="SECTION E: QUALITATIVE FEEDBACK (Participant and/or Caregiver)", 
                                            closable=False, default_open=True):
                        dpg.add_spacer(height=3)

                        # Question 1
                        dpg.add_text("1. How did you find the experience with the device and the interventions?")
                        dpg.add_input_text(width=1000, height=60, multiline=True)

                        # Question 2
                        dpg.add_text("2. Did you notice any improvements in your daily life?")
                        dpg.add_input_text(width=1000, height=60, multiline=True)

                        # Question 3
                        dpg.add_text("3. Were there any discomforts or concerns?")
                        dpg.add_input_text(width=1000, height=60, multiline=True)

                        # Question 4
                        dpg.add_text("4. Suggestions for improvement?")
                        dpg.add_input_text(width=1000, height=60, multiline=True)


    def _get_date_today(self):
        now = datetime.now()

        # GUI String Format
        self.formatted_today_str = now.strftime("%m/%d/%Y")

        # DPG Date Picker String Format
        self.today_dict = {
            'month_day': now.day,
            'month': now.month - 1,     # DPG months are 0-11
            'year': now.year - 1900     # DPG years are counted since 1900
        }

    ### Callbacks
    def date_picker_callback(self, sender, app_data, user_data):
        if app_data is not None:
            year = app_data['year'] + 1900
            month = app_data['month'] + 1
            day = app_data['month_day']
            
            formatted_date = f"{month:02d}/{day:02d}/{year}"
            
            dpg.set_value(f"{self.tag}_date_input_field", formatted_date)
        
        dpg.configure_item(f"{self.tag}_date_popup", show=False)



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

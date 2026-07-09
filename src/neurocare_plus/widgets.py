import math
import dearpygui.dearpygui as dpg

import view_elements


class WidgetManager:

    def __init__(self):
        # Setup Hidden Staging Window
        self.build_hidden_staging_window()

        # Initialize Widgets
        self.widgets = {
             "EEG_widget": EEGPlot("EEG_widget", parent="hidden_stage"),
             "PPG_widget": PPGPlot("PPG_widget", parent="hidden_stage"),
             "IMU_widget": view_elements.DynamicPlot("IMU_widget", "IMU", 
                                                   height=0, parent="hidden_stage")
        }

    def build_hidden_staging_window(self):
            with dpg.window(tag="hidden_stage", no_move=True, no_resize=True, show=False): 
                pass


class EEGPlot:

    combo2vertscale_dict = {
        "50 uV": 50,
        "100 uV": 100,
        "200 uV": 200,
        "400 uV": 400,
        "1000 uV": 1000,
        "10000 uV": 10000,
        "Auto": None
    }
        
    combo2twindow_dict = {
        "1 sec": 1,
        "3 sec": 3,
        "5 sec": 5,
        "10 sec": 10,
        "20 sec": 20,
    }

    def __init__(self, tag, parent=0, height=0):
        self.tag = tag
        self.height = height
        self.parent = parent
        self.is_collapsing_header_open = False

        self.eeg_ch_plot = view_elements.UnitChannelPlot('eeg')
        self.en_eeg_ch= {i: view_elements.EnEEGChannel(channel_num=i) for i in range(1,17)}

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
                    with dpg.group(tag="eeg_header_channels_wrapper"):
                        with dpg.collapsing_header(indent=4, label="Channel Options", tag="eeg_header_channels"):
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
            with dpg.child_window(border=False, tag="eeg_plots_parent", height=-45, no_scrollbar=True):
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


class PPGPlot:

    combo2vertscale_dict = {
        "50 uV": 50,
        "100 uV": 100,
        "200 uV": 200,
        "400 uV": 400,
        "1000 uV": 1000,
        "10000 uV": 10000,
        "Auto": None
    }
        
    combo2twindow_dict = {
        "1 sec": 1,
        "3 sec": 3,
        "5 sec": 5,
        "10 sec": 10,
        "20 sec": 20,
    }

    def __init__(self, tag, parent=0, height=0):  # There should be number of channels in init
        self.tag = tag
        self.height = height
        self.parent = parent

        self.ppg_ch_plot = view_elements.UnitChannelPlot('ppg')

        self.build()

    def build(self):
        with dpg.child_window(tag=self.tag, border=True, height=self.height, width=-1, parent=self.parent):

            # Collapsing Header
            with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit, tag="ppg_options_table"):
                dpg.add_table_column(width_stretch=True) # Full width for the header
                dpg.add_table_column(width_fixed=True)   # Tight fit for the button
                dpg.add_table_column(width_fixed=True)
                
                with dpg.table_row():
                    # 1st Column
                    dpg.add_spacer(height=1)
                        
                    # 2nd Column
                    with dpg.group(horizontal=True, indent=4):
                        dpg.add_combo(items=["Auto","50 uV","100 uV","200 uV","400 uV","1000 uV","10000 uV"],
                                      default_value="Auto", tag="combo_ppg_vert_scale", width=80,
                                      callback=self.vert_scale_callback)
                    
                    # 3rd Column
                    dpg.add_combo(items=["1 sec","3 sec","5 sec","10 sec","20 sec"], 
                                  default_value="5 sec", tag="combo_ppg_time_window", width=80,
                                  callback=self.time_window_callback)

            # Spacer
            dpg.add_spacer(height=1)

            # Plotting All 3 Channels
            with dpg.child_window(border=False, tag="ppg_plots_parent", height=-45):
                for i in range(1,4):
                    self.ppg_ch_plot.build(channel_num=i,height=100)

            # Default Value Callback
            self.vert_scale_callback(None, "Auto", None)
            self.time_window_callback(None, "5 sec", None)

    def vert_scale_callback(self, sender, app_data, user_data):
        VERT_SCALE = self.combo2vertscale_dict[app_data]
        if VERT_SCALE:
            for channel_num in range(1,4):
                dpg.set_axis_limits(f"ppg_ch{channel_num}_y_axis",-VERT_SCALE,VERT_SCALE)

    def time_window_callback(self, sender, app_data, user_data):
        WINDOW_TIME = self.combo2twindow_dict[app_data]
        for channel_num in range(1,4):
            dpg.set_axis_limits(f"ppg_ch{channel_num}_x_axis", -WINDOW_TIME  , 0)
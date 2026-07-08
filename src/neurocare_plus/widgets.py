import math
import dearpygui.dearpygui as dpg

import view_elements


class WidgetManager:

    def __init__(self):
        # Setup Hidden Staging Window
        self.build_hidden_staging_window()

        # Initialize Widgets
        self.widgets = {
             "EEG_widget": view_elements.EEGPlot("EEG_widget", parent="hidden_stage"),
             "PPG_widget": view_elements.PPGPlot("PPG_widget", parent="hidden_stage"),
             "IMU_widget": view_elements.DynamicPlot("IMU_widget", "IMU", 
                                                   height=0, parent="hidden_stage")
        }

    def build_hidden_staging_window(self):
            with dpg.window(tag="hidden_stage", no_move=True, no_resize=True, show=False): 
                pass
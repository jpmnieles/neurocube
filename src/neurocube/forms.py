import dearpygui.dearpygui as dpg
from datetime import datetime


class DatePickerField:
    def __init__(self, tag, label):
        self.input_tag = f"{tag}_date_input_field"
        self.popup_tag = f"{tag}_date_popup"
        self.label = label

        now = datetime.now()
        self.default_value = now.strftime("%m/%d/%Y")
        self.today_dict = {
            "month_day": now.day,
            "month": now.month - 1,
            "year": now.year - 1900,
        }

    def build(self):
        self.build_input()
        self.build_popup()

    def build_input(self):
        with dpg.group(horizontal=True):
            if self.label:
                dpg.add_text(f"{self.label}: ")
            dpg.add_input_text(
                tag=self.input_tag,
                default_value=self.default_value,
                readonly=True,
                width=80,
            )

        with dpg.item_handler_registry() as handler_registry:
            dpg.add_item_clicked_handler(
                dpg.mvMouseButton_Left,
                callback=self._position_popup,
            )
        dpg.bind_item_handler_registry(self.input_tag, handler_registry)

    def build_popup(self):
        with dpg.window(
            tag=self.popup_tag,
            popup=True,
            show=False,
            autosize=True,
            no_title_bar=True,
            no_resize=True,
            no_move=True,
        ):
            dpg.add_date_picker(
                level=dpg.mvDatePickerLevel_Day,
                default_value=self.today_dict,
                callback=self.callback,
            )

    def _position_popup(self, sender, app_data, user_data):
        x, y = dpg.get_item_rect_min(self.input_tag)
        _, height = dpg.get_item_rect_size(self.input_tag)
        dpg.set_item_pos(self.popup_tag, [x, y + height])
        dpg.configure_item(self.popup_tag, show=True)

    def callback(self, sender, app_data, user_data):
        if app_data is None:
            return

        year = app_data["year"] + 1900
        month = app_data["month"] + 1
        day = app_data["month_day"]
        dpg.set_value(self.input_tag, f"{month:02d}/{day:02d}/{year}")
        dpg.configure_item(self.popup_tag, show=False)


class PatientOverviewTab:
    def __init__(self):
        self.tag = "patient_overview"
        self.enrollment_date = DatePickerField(
            f"{self.tag}_enrollment",
            "Date of Enrollment",
        )

    def build(self):
        with dpg.tab(label="Patient Overview"):
            with dpg.child_window(height=0):
                #----- New, Edit, Save Buttons -----
                with dpg.group(horizontal=True):
                    dpg.add_button(label="New", width=65, height=30, tag=f"{self.tag}_new_btn")
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
                        dpg.add_input_text(width=57)

                        dpg.add_spacer(width=10)

                        dpg.add_text("Cohort: ")
                        dpg.add_input_int(width=100)

                        dpg.add_spacer(width=10)

                        self.enrollment_date.build()

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

                    #----- Spacers for Search Bar & Forms -----
                    dpg.add_spacer(height=10)
                    dpg.add_separator()
                    dpg.add_spacer(height=2)

                    # SECTION: DATABASE AND DATA COLLECTION
                    with dpg.collapsing_header(label="DATABASE AND DATA COLLECTION", 
                                                closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000,
                            policy=dpg.mvTable_SizingStretchSame):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Date Modified", width_fixed=True, init_width_or_weight=140)
                            dpg.add_table_column(label="Administered by", width_stretch=True)
                            dpg.add_table_column(label="Encoded By", width_stretch=True)

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row():
                                dpg.add_text("10/23/2026")
                                dpg.add_text("Dr. First Name Last Name")
                                dpg.add_text("First Name Last Name")

                        dpg.add_spacer(height=15)

                    # SECTION: MMSE
                    with dpg.collapsing_header(label="MMSE", 
                                                closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000,
                            policy=dpg.mvTable_SizingStretchSame):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Number", width_fixed=True, init_width_or_weight=60)
                            dpg.add_table_column(label="Date", width_stretch=True)
                            dpg.add_table_column(label="Score", width_stretch=True)
                            dpg.add_table_column(label="Administered by", width_stretch=True)
                            dpg.add_table_column(label="Encoded By", width_stretch=True)

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row():
                                dpg.add_text("1")
                                dpg.add_text("10/23/2026")
                                dpg.add_text("25")
                                dpg.add_text("Dr. First Name Last Name")
                                dpg.add_text("First Name Last Name")

                        dpg.add_spacer(height=15)

                    # SECTION: MOCA
                    with dpg.collapsing_header(label="MOCA", 
                                                closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000,
                            policy=dpg.mvTable_SizingStretchSame):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Number", width_fixed=True, init_width_or_weight=60)
                            dpg.add_table_column(label="Date", width_stretch=True)
                            dpg.add_table_column(label="Score", width_stretch=True)
                            dpg.add_table_column(label="Administered by", width_stretch=True)
                            dpg.add_table_column(label="Encoded By", width_stretch=True)

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row():
                                dpg.add_text("1")
                                dpg.add_text("10/23/2026")
                                dpg.add_text("25")
                                dpg.add_text("Dr. First Name Last Name")
                                dpg.add_text("First Name Last Name")

                        dpg.add_spacer(height=15)

                    # SECTION: USER COMFORT EVALUATION
                    with dpg.collapsing_header(label="USER COMFORT EVALUATION", 
                                                closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000,
                            policy=dpg.mvTable_SizingStretchSame):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Number", width_fixed=True, init_width_or_weight=60)
                            dpg.add_table_column(label="Date", width_stretch=True)
                            dpg.add_table_column(label="Administered by", width_stretch=True)
                            dpg.add_table_column(label="Encoded By", width_stretch=True)

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row():
                                dpg.add_text("1")
                                dpg.add_text("10/23/2026")
                                dpg.add_text("Dr. First Name Last Name")
                                dpg.add_text("First Name Last Name")

                        dpg.add_spacer(height=15)

                    # SECTION: INCIDENT REPORT
                    with dpg.collapsing_header(label="INCIDENT REPORT", 
                                                closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000,
                            policy=dpg.mvTable_SizingStretchSame):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Number", width_fixed=True, init_width_or_weight=60)
                            dpg.add_table_column(label="Date", width_stretch=True)
                            dpg.add_table_column(label="Medical OIC", width_stretch=True)
                            dpg.add_table_column(label="Encoded By", width_stretch=True)

                            # Add the row contents
                            ## Row 1
                            with dpg.table_row():
                                dpg.add_text("1")
                                dpg.add_text("10/23/2026")
                                dpg.add_text("Dr. First Name Last Name")
                                dpg.add_text("First Name Last Name")

                        dpg.add_spacer(height=15)


class DatabaseFormTab:

    def __init__(self):
        self.tag = "database_form"
        self.enrollment_date = DatePickerField(
            f"{self.tag}_enrollment",
            "Date of Enrollment",
        )
        self.session_dates = [
            DatePickerField(f"{self.tag}_session_{session}_date", "")
            for session in range(1, 6)
        ]

    def build(self):
        with dpg.tab(label="Database Form"):
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
                        dpg.add_input_text(width=57)

                        dpg.add_spacer(width=10)

                        self.enrollment_date.build()

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
                                dpg.add_radio_button(
                                    items=["Yes", "No", "N/A"],
                                    horizontal=True,
                                )
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 2
                            with dpg.table_row(height=10):
                                dpg.add_text("History of stroke/TBI/epilepsy")
                                dpg.add_radio_button(
                                    items=["Yes", "No", "N/A"],
                                    horizontal=True,
                                )
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 3
                            with dpg.table_row(height=10):
                                dpg.add_text("Visual or auditory impairment")
                                dpg.add_radio_button(
                                    items=["Yes", "No", "N/A"],
                                    horizontal=True,
                                )
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 4
                            with dpg.table_row(height=10):
                                dpg.add_text("Using pacemaker or implanted devices")
                                dpg.add_radio_button(
                                    items=["Yes", "No", "N/A"],
                                    horizontal=True,
                                )
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 5
                            with dpg.table_row(height=10):
                                dpg.add_text("Taking psychoactive  medications")
                                dpg.add_radio_button(
                                    items=["Yes", "No", "N/A"],
                                    horizontal=True,
                                )
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
                                self.session_dates[0].build_input()
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_radio_button(items=["Yes", "No"], horizontal=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 2
                            with dpg.table_row(height=10):
                                dpg.add_text("2")
                                self.session_dates[1].build_input()
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_radio_button(items=["Yes", "No"], horizontal=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 3
                            with dpg.table_row(height=10):
                                dpg.add_text("3")
                                self.session_dates[2].build_input()
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_radio_button(items=["Yes", "No"], horizontal=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 4
                            with dpg.table_row(height=10):
                                dpg.add_text("4")
                                self.session_dates[3].build_input()
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_radio_button(items=["Yes", "No"], horizontal=True)
                                dpg.add_input_text(width=-1, multiline=True)

                            ## Row 5
                            with dpg.table_row(height=10):
                                dpg.add_text("5")
                                self.session_dates[4].build_input()
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_input_text(width=-1, multiline=True)
                                dpg.add_radio_button(items=["Yes", "No"], horizontal=True)
                                dpg.add_input_text(width=-1, multiline=True)

                        for session_date in self.session_dates:
                            session_date.build_popup()

                    dpg.add_spacer(height=15)
                    
                    # SECTION D: POST-INTERVENTION ASSESSMENTS
                    with dpg.collapsing_header(label="SECTION D: POST-INTERVENTION ASSESSMENTS", 
                                            closable=False, default_open=True):
                        dpg.add_spacer(height=3)
                        
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                            borders_innerV=True, borders_outerV=True, width=1000):
                    
                            # Add the columns with label
                            dpg.add_table_column(label="Assessment Tool")
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

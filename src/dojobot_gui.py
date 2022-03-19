import json
import os
import queue
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from dojobot import DojoBot
from PIL import ImageTk, Image
from helper_functions import (
    KEY_LIST, 
    SCREENSHOT_GUIDE_TEXT,
    STAGE_NAMES,
    IMAGE_NAMES,
    STATISTICS_COLUMNS
)
app = ""
fontlight = ('Trebuchet MS', '9', 'normal roman')
fontbold = ('Trebuchet MS', '9', 'bold roman')
settings_tab_rows = {"stage_limit": 1, "run_limit": 2,
                     "channel_run_limit": 3, "channel_start": 4,
                     "main_att_key": 5, "main_att_type": 6, 
                     "main_dur": 7, "burst_stages": 8,
                     "burst_buff_keys": 9, "burst_att_key": 10,
                     "burst_att_type": 11, "burst_dur": 12,
                     "potion_keys": 13, "buff_keys": 14,
                     "stage_walk": 15, "exit_walk": 16
                    }
row_padding = 3


class MainApplication(tk.Frame):
    """ Main GUI class for the bot """

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        # Creating tab layout and saving tabs into self.
        self.tabs = self.create_tabs()
        self.create_styles()
        self.stage_index = 0
        # Populating tabs with labels, buttons, inputs and such.
        self.populate_tabs()
        # Marking configuration unvalidated
        self.valid_conf = False
        self.configuration = dict()
        

    def create_styles(self):
        """ Creates and applies styles to various elements. """

        # Setting window size
        self.parent.geometry('%dx%d+%d+%d' % (500, 620, 1370, 300))
        # Setting window title
        self.parent.title("DojoBeater")
        # Adding custom cursor
        self.parent.configure(cursor = "@MapleCursor.ani")

        # Adding background image 
        # Add image file
        bg = tk.PhotoImage(file = "blurrybg.png")
        # Adding app icon
        self.parent.iconbitmap('icon-png.ico')
        # Show image using labels
        for tab in self.tabs:
            bg_image = tk.Label(tab, image = bg)
            bg_image.photo = bg
            bg_image.place(x = 0, y = 0)
        
        # Label styles
        ttk.Style().configure('Title.TLabel', background='white', 
                              foreground = 'black', font= fontbold)
        ttk.Style().configure('TLabel', background = 'white', 
                              foreground = '#222222', font= fontlight)
        ttk.Style().configure('Error.TLabel', foreground = '#B31A1A', font = fontbold)
        ttk.Style().configure('Attention.TLabel', foreground = '#C5440D', font = fontbold)
        ttk.Style().configure('Valid.TLabel', foreground = 'green', font = fontbold)
        ttk.Style().configure('Found.TLabel', foreground = 'green', font = fontlight)
        ttk.Style().configure('Missing.TLabel', foreground = '#B31A1A', font = fontlight)
        # OptionMenu style
        ttk.Style().configure('TMenubutton', font = fontlight)
        # Button styles
        ttk.Style().configure('TButton', font = fontlight)
        ttk.Style().configure('Start.TButton', foreground = 'green', font = fontlight)
        ttk.Style().configure('Stop.TButton', foreground = 'red', font= fontlight)
        

    def create_tabs(self):
        """ Creates tabbed layout and returns both tabs in a tuple.  """

        tabControl = ttk.Notebook(self.parent)        
        main_tab = ttk.Frame(tabControl)
        settings_tab = ttk.Frame(tabControl)
        misc_tab = ttk.Frame(tabControl)
        tabControl.add(main_tab, text ='Bot')
        tabControl.add(settings_tab, text ='Settings')
        tabControl.add(misc_tab, text = 'Misc.')
        tabControl.pack(expand = 1, fill ="both")
        return (main_tab,settings_tab,misc_tab)
    
    def populate_tabs(self):
        """ Adds GUI components to each tab. """
        
        main_tab = self.tabs[0]
        settings_tab = self.tabs[1]
        misc_tab = self.tabs[2]
        
        ####
        # Main tab bot controls
        ####
        # Bot control label
        ttk.Label(main_tab, style = "Title.TLabel",
                text ="Bot controls").grid(column = 0, 
                                    row = 0,
                                    padx = 10, sticky = tk.W)
        button_frame = ttk.Frame(main_tab, name = "bot_control_buttons")
        # Start bot button
        ttk.Button(button_frame,
                name = "start_bot_button",
                state = "disabled",
                text ="Start bot",
                command = self.start_bot_callback, width = 15, style="Start.TButton").pack(padx = 3, pady = 5)
        # Stop bot button
        ttk.Button(button_frame,
                name = "stop_bot_button",
                state = "disabled",
                text ="Stop bot",
                command = self.stop_bot_callback, width = 15, style="Stop.TButton").pack(padx = 3, pady = 5)
        # Bot control button frame
        button_frame.grid(column = 0, row = 1, padx = 10, sticky= tk.W)

        ####
        # Main tab statistics
        ####
        ttk.Label(main_tab, style = "Title.TLabel",
                text ="Statistics").grid(column = 0, 
                                    row = 2,
                                    pady = 20,
                                    padx = 10,
                                    sticky = tk.W)
        stat_canvas = tk.Canvas(main_tab, width = 100, height = 250)
        stat_canvas.grid(column = 0, row = 3, padx = 10, sticky = tk.W)

        ####
        # Main tab statistics tree view
        ####
        # Defining columns
        stat_columns = ("desc", "value")
        # Creating TreeView object
        stat_tree = ttk.Treeview(stat_canvas, columns=stat_columns, show='headings')
        # Setting headings
        stat_tree.heading("desc", text="Item")
        stat_tree.heading("value", text="Value")
        # Setting constraints to headings and columns
        stat_tree.column("desc", anchor="w", minwidth=0, width=130, stretch=tk.NO)
        stat_tree.column("value", anchor="w", minwidth=0, width=85, stretch=tk.NO)

        # Inserting Items
        for key_val in STATISTICS_COLUMNS.keys():
            # Putting key into array
            packed_val = [key_val, '---']
            # Inserting column value into treeview
            stat_tree.insert('', tk.END, values=packed_val)
        stat_tree.grid(row=0, column=0, sticky='w')
        self.statistics_tree = stat_tree

        ####
        # Main tab bot status
        ####

        ttk.Label(main_tab, style = "Title.TLabel",
                text="Bot status").grid(column = 1,
                                        row = 0,
                                        pady = 20)
        status_canvas = tk.Canvas(main_tab, width = 250, height = 90)
        # Creating rectangle to hold text
        status_canvas.create_rectangle(2, 2, 250, 90, fill = 'white')
        # Placing canvas into grid.
        status_canvas.grid(column = 1, row = 1)
        # Saving status canvas into self.
        self.status_canvas = status_canvas

        # Settings tab labels
        ttk.Label(settings_tab,
                text ="Bot settings", style = "Title.TLabel",
                justify=tk.LEFT, anchor = "w").grid(column = 0,
                                                    row = 0,
                                                    sticky=tk.W, 
                                                    padx = 5,
                                                    pady = 20)
        # Exit after stage
        ttk.Label(settings_tab, text = "Exit after stage:", name = "stage_limit_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["stage_limit"],
                                                        sticky = tk.W,
                                                        padx = 5)
        exit_after_stage = ttk.Entry(settings_tab, width = 3,
                                     font = fontlight, name = "stage_limit",
                                     validate="key", validatecommand = self.conf_changed)
        exit_after_stage.grid(column = 1, row = settings_tab_rows["stage_limit"],
                              pady = row_padding, sticky = tk.W)
        ##################

        # Total run count limit
        ttk.Label(settings_tab, text = "Run count limit:", name = "run_limit_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["run_limit"],
                                                        sticky = tk.W,
                                                        padx = 5)
        count_limit = ttk.Entry(settings_tab, width = 4, font = fontlight, name = "run_limit",
                                validate="key", validatecommand = self.conf_changed)
        count_limit.grid(column = 1, row = settings_tab_rows["run_limit"],
                         pady = row_padding, sticky = tk.W)
        ##################

        # Run count per channel limit
        ttk.Label(settings_tab, text = "Channel run limit:", name = "channel_run_limit_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["channel_run_limit"],
                                                        sticky = tk.W,
                                                        padx = 5)
        count_limit = ttk.Entry(settings_tab, width = 4, font = fontlight, name = "channel_run_limit",
                                validate="key", validatecommand = self.conf_changed)
        count_limit.grid(column = 1, row = settings_tab_rows["channel_run_limit"],
                         pady = row_padding, sticky = tk.W)
        ##################

        # Starting channel
        ttk.Label(settings_tab, text = "Starting channel:", name = "channel_start_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["channel_start"],
                                                        sticky = tk.W,
                                                        padx = 5)
        count_limit = ttk.Entry(settings_tab, width = 4, font = fontlight, name = "channel_start",
                                validate="key", validatecommand = self.conf_changed)
        count_limit.grid(column = 1, row = settings_tab_rows["channel_start"],
                         pady = row_padding, sticky = tk.W)
        ##################
        
        # Main attack key
        ttk.Label(settings_tab, text = "Main att. key:", name = "main_att_key_lbl",
                  justify=tk.LEFT, anchor = "w").grid(column = 0, row = settings_tab_rows["main_att_key"],
                                     sticky = tk.W, padx = 5)
        main_att_key = ttk.Entry(settings_tab, width = 6, font = fontlight, name = "main_att_key",
                                 validate="key", validatecommand = self.conf_changed)
        main_att_key.grid(column = 1, row = settings_tab_rows["main_att_key"],
                          pady = row_padding, sticky = tk.W)
        ##################

        # Main attack type
        ttk.Label(settings_tab, text = "Main att. type:", name = "main_att_type_lbl",
                  justify=tk.LEFT, anchor = "w").grid(column = 0, row = settings_tab_rows["main_att_type"],
                                     sticky = tk.W, padx = 5)
        # Main attack type string variable
        self.main_att_var = tk.StringVar(settings_tab)
        main_att_type_options = ['Press', 'Hold']
        self.main_att_var.set(main_att_type_options[0])
        self.main_att_var.trace('w', self.main_att_type_listener)
        # Main attack type dropdown
        main_att_dd = ttk.OptionMenu(settings_tab, self.main_att_var,
                                       main_att_type_options[0], 
                                       *main_att_type_options, command=self.conf_changed)
        main_att_dd.configure(width = 8, cursor = "@MapleCursor_Link.ani")
        main_att_dd.grid(column = 1, row = settings_tab_rows["main_att_type"],
                         pady = row_padding, sticky = tk.W)
        ##################
        
        # Burst stages
        ttk.Label(settings_tab, text = "Burst stages:", name = "burst_stages_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["burst_stages"],
                                                        sticky = tk.W,
                                                        padx = 5)
        burst_stages = ttk.Entry(settings_tab, width = 14, font = fontlight, name = "burst_stages",
                                 validate="key", validatecommand = self.conf_changed)
        burst_stages.grid(column = 1, row = settings_tab_rows["burst_stages"],
                          pady = row_padding, sticky = tk.W)
        ##################

        # Burst buff keybinds
        ttk.Label(settings_tab, text = "Burst buff keys:", name = "burst_buff_keys_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["burst_buff_keys"],
                                                        sticky = tk.W,
                                                        padx = 5)
        burst_buff_keys = ttk.Entry(settings_tab, width = 16, font = fontlight, name = "burst_buff_keys",
                                    validate="key", validatecommand = self.conf_changed)
        burst_buff_keys.grid(column = 1, row = settings_tab_rows["burst_buff_keys"],
                             pady = row_padding, sticky = tk.W)
        ##################

        # Burst attack keybind
        ttk.Label(settings_tab, text = "Burst att. key:", name = "burst_att_key_lbl",
                  justify=tk.LEFT, anchor = "w").grid(column = 0, row = settings_tab_rows["burst_att_key"],
                                     sticky = tk.W, padx = 5)
        burst_att_key = ttk.Entry(settings_tab, width = 6, font = fontlight, name = "burst_att_key",
                                  validate="key", validatecommand = self.conf_changed)
        burst_att_key.grid(column = 1, row = settings_tab_rows["burst_att_key"],
                           pady = row_padding, sticky = tk.W)

        # Burst attack type
        ttk.Label(settings_tab, text = "Burst att. type:", name = "burst_att_type_lbl",
                  justify=tk.LEFT, anchor = "w").grid(column = 0,
                                                      row = settings_tab_rows["burst_att_type"],
                                                      sticky = tk.W,
                                                      padx = 5)
        self.burst_att_var = tk.StringVar(settings_tab, name = "burst_att_type")
        burst_att_options = ['Press once', 'Hold', 'Press repeatedly']
        self.burst_att_var.set(burst_att_options[0])
        self.burst_att_var.trace("w", self.burst_att_type_listener)
        burst_att_dd = ttk.OptionMenu(settings_tab, self.burst_att_var, 
                                      burst_att_options[0], *burst_att_options, command=self.conf_changed)
        burst_att_dd.configure(width = 15, cursor = "@MapleCursor_Link.ani")
        burst_att_dd.grid(column = 1, row = settings_tab_rows["burst_att_type"],
                          pady = row_padding, sticky = tk.W)
        #####################

        # Potion keys
        ttk.Label(settings_tab, text = "Potion keys:", name = "potion_keys_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["potion_keys"],
                                                        sticky = tk.W,
                                                        padx = 5)
        potion_keys = ttk.Entry(settings_tab, width = 10, font = fontlight, name = "potion_keys",
                                validate="key", validatecommand = self.conf_changed)
        potion_keys.grid(column = 1, row = settings_tab_rows["potion_keys"],
                         pady = row_padding, sticky = tk.W)
        #####################

        # Buff keys
        ttk.Label(settings_tab, text = "Buff keys:", name = "buff_keys_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["buff_keys"],
                                                        sticky = tk.W,
                                                        padx = 5)
        buff_keys = ttk.Entry(settings_tab, width = 20, font = fontlight, name = "buff_keys",
                              validate="key", validatecommand = self.conf_changed)
        buff_keys.grid(column = 1, row = settings_tab_rows["buff_keys"],
                       pady = row_padding, sticky = tk.W)
        #####################

        # Stage portal walk duration
        ttk.Label(settings_tab, text = "Stage walk for:", name = "stage_walk_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["stage_walk"],
                                                        sticky = tk.W,
                                                        padx = 5)
        ttk.Entry(settings_tab, width = 5,
                  font = fontlight,
                  validate="key", validatecommand = self.conf_changed,
                  name = "stage_walk").grid(column = 1,
                                             row = settings_tab_rows["stage_walk"],
                                             pady = row_padding, sticky = tk.W)
        #####################

        # Exit stage portal walk duration
        ttk.Label(settings_tab, text = "Exit walk for:", name = "exit_walk_lbl",
                  justify = tk.LEFT, anchor = "w").grid(column = 0,
                                                        row = settings_tab_rows["exit_walk"],
                                                        sticky = tk.W,
                                                        padx = 5)
        ttk.Entry(settings_tab, width = 5,
                  font = fontlight,
                  validate="key", validatecommand = self.conf_changed,
                  name = "exit_walk").grid(column = 1,
                                             row = settings_tab_rows["exit_walk"],
                                             pady = row_padding, sticky = tk.W)
        #####################

        # Name of configuration file
        ttk.Label(settings_tab, text = "Configuration file name",  name = "config_name_lbl",
                  style = "Title.TLabel", justify = tk.LEFT,
                  anchor = "w").grid(column = 2, row = 0,
                                     sticky = tk.W,
                                     padx = 5)
        config_name = ttk.Entry(settings_tab, width = 15, font = fontlight, name = "config_name")
        config_name.grid(column = 2, row = 1, padx = 5, sticky = tk.W)
        ##########################

        # Save configuration button
        ttk.Button(settings_tab, command = self.save_configuration,
                text ="Save configuration").grid(column = 2, row = 2, padx = 5, sticky = tk.W)
        #########################

        # Load configuration button
        ttk.Button(settings_tab, command = self.load_configuration,
                text ="Load configuration").grid(column = 2, row = 3, padx = 5, sticky = tk.W)
        #########################

        # Validate configuration button
        self.validate_conf_btn = ttk.Button(settings_tab, command = self.check_configuration,
                                          state="enabled",
                                          text = "Validate configuration")
        self.validate_conf_btn.grid(column = 2, row = 4, padx = 5, sticky = tk.W)
        #########################
        
        # Validation status label
        self.validate_lbl = ttk.Label(settings_tab, text = "Unvalidated configuration",
                                    style = "Attention.TLabel")
        self.validate_lbl.grid(column = 2, 
                             row = 6,
                             padx = 5,
                             sticky = tk.W)
        ##########################

        # Misc. tab

        # Stage screenshots title label
        ttk.Label(misc_tab, text = "Stage screenshots",
                style = "Title.TLabel").grid(column = 0, 
                                             row = 0,
                                             padx = 5,
                                             pady = 20,
                                             sticky = tk.W)
        # Instruction label
        ttk.Label(misc_tab, text = SCREENSHOT_GUIDE_TEXT, wraplength=450
                ).grid(column = 0,
                       columnspan=8,
                       row = 1,
                       padx = 5,
                       sticky = tk.W)
        ###############################

        # Stage name prefix label
        ttk.Label(misc_tab, style = "Title.TLabel", text = "Stage name:").grid(column = 0, row = 2,
                                                       padx = 5,
                                                       pady = row_padding,
                                                       sticky = tk.W)
        # Stage name label                            
        self.stage_name = ttk.Label(misc_tab, text = STAGE_NAMES[self.stage_index])
        self.stage_name.grid(column = 1, row = 2,
                             padx = 5,
                             pady = 10,
                             sticky = tk.W)
        ##############################

        # Stage changer buttons
        ttk.Button(misc_tab, command = self.previous_stage_name, width = 15,
                   text = "<- Previous stage").grid(column = 0, row = 3,
                                                    padx = 5, pady = row_padding,
                                                    sticky = tk.W)
        ttk.Button(misc_tab, command = self.next_stage_name, width = 15,
                   text = "Next stage ->").grid(column = 1, row = 3,
                                                padx = 5, pady = row_padding,
                                                sticky = tk.W)
        ########################

        # Screenshot button
        ttk.Button(misc_tab, command = self.take_stage_screenshot, width = 15,
                   text = "Take screenshot").grid(column = 0, row = 4,
                                                  padx = 5, pady = row_padding,
                                                  sticky = tk.W)
        ########################

        # Screenshot canvas
        self.sc_canvas = tk.Canvas(misc_tab, width=0, height = 0, name = "sc_canvas")
        self.sc_canvas.grid(column = 0, row = 6,
                            columnspan=5,
                            padx = 5, pady = row_padding,
                            sticky = tk.W)
        ttk.Label(misc_tab, style = "Title.TLabel", text = "Stage name screenshot:").grid(column = 0, row = 5, 
                                                               padx = 5, pady = row_padding,
                                                               sticky = tk.W)
        self.show_stage_image()

        ########################

        # Required images label
        ttk.Label(misc_tab, style = "Title.TLabel", text = "Required helper images:").grid(column = 0, row = 7,
                  padx = 5,
                  pady = row_padding,
                  sticky = tk.W)
        # Creating labels for each required image
        self.create_required_images_list(misc_tab, 8)
        #########################
        
        
    def create_required_images_list(self, tab, start_from_row):
        """ Creates labels for each required image and colors them depending on if they exist. """

        if os.path.exists("images"):
            for image_name in IMAGE_NAMES:
                if os.path.exists("images/" + image_name + ".png"):
                    ttk.Label(tab, text = image_name + ".png found.",
                            style = "Found.TLabel").grid(row = start_from_row,
                                                                column = 0, padx = 5,
                                                                sticky = tk.W)
                else:
                    ttk.Label(tab, text = image_name + ".png missing.", 
                            style = "Missing.TLabel").grid(row = start_from_row,
                                                            column = 0, padx = 5,
                                                            sticky = tk.W)
                start_from_row += 1
        else:
            ttk.Label(tab, text = "Folder \"images\" not found in root directory.",
                    style = "Error.TLabel").grid(row = start_from_row, columnspan=4,
                                                        column = 0, padx = 5,
                                                        sticky = tk.W)
    def previous_stage_name(self):
        """ Changes text on stage name label to previous stage. """
        
        if self.stage_index > 0:
            self.stage_index -= 1
            if STAGE_NAMES[self.stage_index] in ['Dojo lobby', 'Buff stage', 'Exit stage']:
                self.stage_name.config(text = STAGE_NAMES[self.stage_index])
            else:
                self.stage_name.config(text = self.make_ordinal(STAGE_NAMES[self.stage_index]))
            
            self.show_stage_image()

    def generate_stage_image_name(self):
        """ Generates name for stage image. """
        # Indexes are a bit strange for a couple of stages,
        # so they have to be checked separately.
        if STAGE_NAMES[self.stage_index] == "Dojo lobby":
            stage_image_name = "stage_-1.png"
        elif STAGE_NAMES[self.stage_index] == "Exit stage":
            stage_image_name = "stage_-2.png"
        elif STAGE_NAMES[self.stage_index] == "Buff stage":
            stage_image_name = "stage_0.png"
        else:
            stage_image_name = "stage_" + str(self.stage_index - 2) + ".png"
        
        return stage_image_name

    def show_stage_image(self):
        """ Displays image of stage map name. """
        stage_image_name = self.generate_stage_image_name()
        try:
            # Deleting possible previous image or text
            self.delete_image_and_text()
            # Trying to open the stage image.
            stage_img = ImageTk.PhotoImage(Image.open("images/" + stage_image_name))
            # Setting canvas dimensions to match image's dimensions.
            self.sc_canvas.config(width = stage_img.width(), height = stage_img.height())
            # Setting img to canvas to avoid garbage collection
            self.sc_canvas.img = stage_img
            # Creating the image
            self.stage_image = self.sc_canvas.create_image(0, 0, anchor = tk.NW, image = stage_img)
        except FileNotFoundError:
            # Resizing canvas
            self.sc_canvas.config(width = 125, height = 20)
            # Setting text to indicate that image doesn't exist for the stage.
            self.not_found_text = self.sc_canvas.create_text(5, 0, anchor="nw", text="Image not found")

    def delete_image_and_text(self):
        """ Deletes stage images or text if they exist. """

        # Deleting stage image if there was one.
        if hasattr(self, 'stage_image'):
            self.sc_canvas.delete(self.stage_image)
        if hasattr(self, 'not_found_text'):
            self.sc_canvas.delete(self.not_found_text)

    def next_stage_name(self):
        """ Changes text on stage name label to next stage. """

        if self.stage_index < len(STAGE_NAMES) - 1:
            self.stage_index += 1
            if STAGE_NAMES[self.stage_index] in ['Dojo lobby', 'Buff stage', 'Exit stage']:
                 self.stage_name.config(text = STAGE_NAMES[self.stage_index])
            else:
                self.stage_name.config(text = self.make_ordinal(STAGE_NAMES[self.stage_index]))
            self.show_stage_image()
            
    def conf_changed(self, *args):
        """ Entry and OptionMenu change listener for configuration inputs. """

        # If conf was valid before, we need to revalidate.
        if self.valid_conf:
            # Setting verify label text as unvalidated
            self.validate_lbl.config(text="Unvalidated configuration", style = "Attention.TLabel")
            # Enabling validation button
            self.validate_conf_btn['state'] = "enabled"
            # Disabling start bot button until conf is revalidated.
            self.tabs[0].nametowidget('bot_control_buttons').nametowidget('start_bot_button')['state'] = 'disabled'
            # Setting configuration as false to prevent this if block from triggering more than once.
            self.valid_conf = False
        return True

    def take_stage_screenshot(self):
        """ Makes bot to take a screenshot of the map name. """

        self.queue = queue.Queue()
        self.process = DojoBot(self, sc_mode = True)
        self.process.start()
        self.parent.after(100, self.process_queue)

    def make_ordinal(self, n):
        ''' Convert an integer into its ordinal representation '''
        n = int(n)
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return str(n) + suffix

    def save_configuration(self):
        """ Saves configuration into JSON file. """

        # Emptying previous configuration.
        self.configuration = dict()
        # Validating user input
        if self.validate_configuration():
            self.validate_lbl.config(text = "Valid configuration", style = "Valid.TLabel")
            self.validate_conf_btn['state'] = "disabled"
            config_name_elem = self.tabs[1].nametowidget("config_name")
            if len(config_name_elem.get().strip()):
                self.configuration['config_name'] = config_name_elem.get()
                file_name = config_name_elem.get() + '.json'
                # Removing old configuration file to make sure overwriting is successful.
                if os.path.exists(file_name):
                    os.remove(file_name)

                # Making a copy of configuration, because one field has to be excluded.
                modified_conf = dict(self.configuration)
                # Removing channel start information
                del modified_conf['channel_start']

                # Writing dictionary into JSON file.
                with open(file_name, 'w') as f:
                    json.dump(modified_conf, f, indent=4, sort_keys=True)
                self.check_configuration()
            else:
                # Setting config name error
                self.set_elem_error(config_name_elem)
        else:
            self.validate_lbl.config(text = "Invalid configuration", style = "Error.TLabel")
            self.validate_conf_btn['state'] = "enabled"

    def load_configuration(self):
        """ Loads configuration from JSON file. """

        settings_tab = self.tabs[1]
        # Creating a file explorer
        file_name = filedialog.askopenfilename(initialdir = __file__,
                                          title = "Select a Configuration File",
                                          filetypes = [("JSON Source File", "*.json")])
        if file_name:
            with open(file_name, 'r') as f:
                self.configuration = json.load(f)
                # Setting values that always exist.
                self.burst_att_var.set(self.configuration['burst_att_type'])
                self.main_att_var.set(self.configuration['main_att_type'])

                # Deleting all previous values.
                for child in settings_tab.winfo_children():
                    # Checking only Entry objects
                    if isinstance(child, ttk.Entry):
                        # Deleting any pre-existing values from the entry
                        child.delete(0, tk.END)
                # Looping over every key
                for key in self.configuration:
                    try:
                        # Getting widget by config key
                        field = settings_tab.nametowidget(key)
                        value = self.configuration[key]
                        # If value is a list, it needs to be comma separated.
                        if isinstance(value, list):
                            value = ','.join([str(i) for i in value])
                        # Inserting value to GUI field.
                        field.insert(0, value)
                    except KeyError:
                        pass
            self.check_configuration()
    
    def check_configuration(self):
        """ Checks that configuration is OK and enables "Start bot" button. """

        buttons = self.tabs[0].nametowidget('bot_control_buttons')
        # If configuration is okay, we can allow the user to start the bot.
        if self.validate_configuration():
            self.validate_lbl.config(text = "Valid configuration", style = "Valid.TLabel")
            self.validate_conf_btn['state'] = "disabled"
            # Enabling start bot button.
            buttons.nametowidget('start_bot_button')['state'] = 'enabled'
        else:
            self.validate_lbl.config(text = "Invalid configuration", style = "Error.TLabel")
            # Disabling start bot button.
            buttons.nametowidget('start_bot_button')['state'] = 'disabled'
             # Enabling start bot button.
            buttons.nametowidget('stop_bot_button')['state'] = 'disabled'

    def validate_configuration(self):
        """ Validates configuration user inputs. """

        settings_tab = self.tabs[1]
        # Flag to keep track if required info is given in right format.
        invalid_elems = []
        # Iterating over every children
        for child in settings_tab.winfo_children():
            # Checking only Entry objects
            if isinstance(child, ttk.Entry):
                elem_label = settings_tab.nametowidget(child.winfo_name() + '_lbl')
                if child.winfo_name() != "config_name":
                    # Removing possible error style from the label.
                    elem_label.configure(style = "TLabel")
                else:
                    elem_label.configure(style = "Title.TLabel")

                value = child.get().lower()
                stripped_value = value.strip()
                # Using pattern matching to catch specific entries.
                match child.winfo_name():
                    case "stage_limit":
                        if len(stripped_value):
                            try:
                                if int(value) > 80:
                                    raise ValueError
                                else:
                                    self.configuration['stage_limit'] = int(value)
                            except ValueError:
                                invalid_elems.append(child)
                    case "run_limit":
                        if len(stripped_value):
                            try:
                                if int(value) < 0:
                                    raise ValueError
                                else:
                                    self.configuration['run_limit'] = int(value)
                            except ValueError:
                                invalid_elems.append(child)
                    case "channel_run_limit":
                        if len(stripped_value):
                            try:
                                if int(value) < 0:
                                    raise ValueError
                                else:
                                    self.configuration['channel_run_limit'] = int(value)
                            except ValueError:
                                invalid_elems.append(child)
                    case "channel_start":
                        if len(stripped_value):
                            try:
                                # Channel has to be from 1 to 10.
                                if int(value) <= 0 or int(value) > 10:
                                    raise ValueError
                                else:
                                    self.configuration['channel_start'] = int(value)
                            except ValueError:
                                invalid_elems.append(child)
                        else:
                            # Value is required, so if it is empty, it's also invalid.
                            invalid_elems.append(child)
                    case "main_att_key":
                        if value not in KEY_LIST:
                            invalid_elems.append(child)
                        else:
                            self.configuration['main_att_key'] = value
                    case "main_dur":
                        try:
                            if self.main_att_var.get() == "Hold" and int(value) < 0:
                                raise ValueError
                            else:
                                self.configuration['main_dur'] = int(value)
                        except ValueError:
                            invalid_elems.append(child)
                    case "burst_stages":
                        if len(stripped_value):
                            # Removing whitespace and commas
                            stripped_and_split = "".join([x.strip() for x in value.split(',')])
                            try:
                                # If int conversion works, then input is valid.
                                int(stripped_and_split)
                                # Making the input string into integer list.
                                self.configuration['burst_stages'] = list(map(int, value.split(',')))
                            except ValueError:
                                # If there were other characters,
                                # int conversion fails and triggers this.
                                invalid_elems.append(child)
                    case "burst_buff_keys":
                        if len(stripped_value):
                            keys = value.replace(" ", "").split(",")
                            self.configuration['burst_buff_keys'] = []
                            for key in keys:
                                if key not in KEY_LIST:
                                    invalid_elems.append(child)
                                else:
                                    self.configuration['burst_buff_keys'].append(key)
                    case "burst_att_key":
                        if len(stripped_value):
                            if value not in KEY_LIST:
                                invalid_elems.append(child)
                            else:
                                self.configuration['burst_att_key'] = value
                    case "burst_dur":
                        try:
                            if self.burst_att_var.get() in ['Hold', 'Press repeatedly'] and int(value) < 0:
                                raise ValueError
                            else:
                                self.configuration['burst_dur'] = int(value)
                        except ValueError:
                            invalid_elems.append(child)
                    case "potion_keys":
                        keys = value.replace(" ", "").split(",")
                        self.configuration['potion_keys'] = []
                        if len(stripped_value):
                            for key in keys:
                                if key not in KEY_LIST:
                                    invalid_elems.append(child)
                                else:
                                    self.configuration['potion_keys'].append(key)
                    case "buff_keys":
                        keys = value.replace(" ", "").split(",")
                        self.configuration['buff_keys'] = []
                        if len(stripped_value):
                            for key in keys:
                                if key not in KEY_LIST:
                                    invalid_elems.append(child)
                                else:
                                    self.configuration['buff_keys'].append(key)
                    case "stage_walk":
                        try:
                            if float(value) <= 0:
                                raise ValueError
                            else:
                                self.configuration['stage_walk'] = float(value)
                        except ValueError:
                            invalid_elems.append(child)
                    case "exit_walk":
                        try:
                            if float(value) <= 0:
                                raise ValueError
                            else:
                                self.configuration['exit_walk'] = float(value)
                        except ValueError:
                            invalid_elems.append(child)
            elif isinstance(child, ttk.OptionMenu):
                self.configuration['main_att_type'] = self.main_att_var.get()
                self.configuration['burst_att_type'] = self.burst_att_var.get()

        if not invalid_elems:
            self.valid_conf = True
            # Resetting statistical value table
            self.reset_stats()
            return True
        else:
            for elem in invalid_elems:
                self.set_elem_error(elem)    
            return False

    def set_elem_error(self, elem):
        """ Adds error style to widget passed as a param. """

        # Getting label that's related to the entry.
        elem_label = self.tabs[1].nametowidget(elem.winfo_name() + '_lbl')
        # Setting an error style to the label.
        elem_label.configure(style = "Error.TLabel")

    def main_att_type_listener(self, *args):
        """ Reacts to changes of main attack type option menu value. """
        
        val = self.main_att_var.get()
        # Destroying possible old entry
        for child in self.tabs[1].winfo_children():
            if child.winfo_name() in ["main_dur_lbl", "main_dur"]:
                child.destroy()
        # If chosen value is hold, show label and entry for duration of hold.
        if val == "Hold":
            ttk.Label(self.tabs[1], text = "Att. duration:*", name = "main_dur_lbl",
                      justify=tk.LEFT, anchor = "w").grid(column = 0, 
                                                          row = settings_tab_rows["main_dur"],
                                                          sticky = tk.W, padx = 5)
            
            ttk.Entry(self.tabs[1], width = 6, font = fontlight,
                      validate="key", validatecommand = self.conf_changed,
                      name = "main_dur").grid(column = 1,
                                              row = settings_tab_rows["main_dur"],
                                              pady = row_padding, sticky = tk.W)

    def burst_att_type_listener(self, *args):
        """ Reacts to changes of option menu value. """

        # Get selected option menu value
        val = self.burst_att_var.get()
        # Deleting press duration entry if it exists.
        for child in self.tabs[1].winfo_children():
            # If child is any of the ones in the list, destroy it.
            if child.winfo_name() in ["burst_dur", "burst_dur_lbl"]:
                child.destroy()

        # If chosen value needs requires additional information, create Label and Entry.
        if val in ["Press repeatedly", "Hold"]:
            ttk.Label(self.tabs[1], text = "Burst duration:*", name = "burst_dur_lbl",
                      justify=tk.LEFT, anchor = "w").grid(column = 0, 
                                                          row = settings_tab_rows["burst_dur"],
                                                          sticky = tk.W, padx = 5)
            ttk.Entry(self.tabs[1], width = 6,
                      font = fontlight,
                      validate="key", validatecommand = self.conf_changed,
                      name = "burst_dur").grid(column = 1, row = settings_tab_rows["burst_dur"],
                                               pady = row_padding, sticky = tk.W)

            
    def update_status(self, message):
        """ Adds a message to bot status box. """
        
        msgs = self.status_canvas.find_withtag("message")
        msg_count = len(msgs)
        y_pos = 5
        # If canvas has messages in it already.
        if msg_count < 5 and msg_count > 0:
            # Calculate y position for new message.
            y_pos = (msg_count * 15) + y_pos
        # Deleting messages after there are too many of them.
        elif msg_count > 4:
            self.status_canvas.delete("message")
            y_pos = 5
        # Creating text element inside canvas.
        self.status_canvas.create_text(5, y_pos, anchor="nw", tags="message",
                                           text = message, fill="black",
                                           font=('Helvetica 8 normal'))
    
    def update_stats(self, stat_key, stat_value):
        """ Updates statistical values into TreeView. 
            param::stat_key
                Key of statistical value, same as dict keys in STATISTICS_COLUMNS
            param::stat_value
                Measured statistical value
        """

        s_tree = self.statistics_tree
        # Getting statistics TreeView children
        children = s_tree.get_children()
        # Looping over children
        for child in children:
            # Getting data of child
            stat_item = s_tree.item(child)
            # Matching value to be updated
            if stat_item['values'][0] == stat_key:
                # Deleting previous value
                s_tree.delete(child)
                # Setting updated values
                updated_values = [stat_item['values'][0], stat_value]
                # Inserting values into tree
                s_tree.insert('', STATISTICS_COLUMNS[stat_key], values = updated_values)

    def reset_stats(self):
        """ Resets statistical values on the treeview. """

        s_tree = self.statistics_tree
        for index, child in enumerate(s_tree.get_children()):
            stat_item = s_tree.item(child)
            s_tree.delete(child)
            updated_values = [stat_item['values'][0], '---']
            s_tree.insert('', index, values = updated_values)

    def process_queue(self):
        try:
            msg = self.queue.get_nowait()
            # Show result of the task if needed
            self.update_status(msg)
        except queue.Empty:
            self.parent.after(100, self.process_queue)

    def set_status(self, message):
        self.update_status(message)
    
    def start_bot_callback(self):
        # Enabling stop button and disabling start button
        self.set_status("Starting bot.")
        buttons = self.tabs[0].nametowidget('bot_control_buttons')
        buttons.nametowidget('stop_bot_button')['state'] = 'enabled'
        buttons.nametowidget('start_bot_button')['state'] = 'disabled'
        self.queue = queue.Queue()
        self.process = DojoBot(self)
        self.process.start()
        self.parent.after(100, self.process_queue)

    def stop_bot_callback(self):
        # Enabling and disabling control buttons
        self.set_status("Stopping bot.")
        buttons = self.tabs[0].nametowidget('bot_control_buttons')
        buttons.nametowidget('stop_bot_button')['state'] = 'disabled'
        buttons.nametowidget('start_bot_button')['state'] = 'enabled'
        self.process.stop_bot()
        self.process.join()
        

        
if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    app.pack(side="top", fill="both", expand=True)
    root.mainloop()
    

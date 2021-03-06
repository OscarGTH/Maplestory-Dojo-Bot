import os
import random
import ctypes
import sys
import threading
import pyautogui as pg
import pydirectinput as pd
import time
import datetime
import pygetwindow as gw
from logzero import logger
from helper_functions import (
    calculate_average_run_time,
    calculate_pph
)

# Tuple for setting the region where map name should be detected from.
# Values are left, top, width, height in order.
MAP_NAME_REGION = (0, 0, 0, 0)
# Maple window region
MAPLE_REGION = ()
MONSTER_HP_REGION = ()
# Contains location of settings button after it's been found once using image detection.
SETTINGS_BTN_LOC = None
# Variable to mark current_stage the player is in.
# (-2 for exit stage, -1 for main lobby, 0 for buff lobby)
current_stage = -3
prev_stage = -3
# Flag to tell if player is alive
player_alive = True
# Attack direction flag
prev_attack_direction = ""
# Used to contain the run start time in UNIX format
start_time = 0
run_time = 0

class DojoBot(threading.Thread):

    def __init__(self, master, sc_mode = False):
            super().__init__()
            self.sc_mode = sc_mode
            self.gui = master
            self.queue = master.queue
            if not self.sc_mode:
                self.configuration = master.configuration
                self.set_up_conf()
                self.run_stats = {'reached_end': False, 'run_count': 0, 
                                  'current_channel': self.configuration['channel_start'],
                                  'channel_run_count': 0, 'bursted_stages': [], 'death_count': 0,
                                  'all_run_times': [], 'npc_not_found_count': 0, 'highest_pph': 0}
                
    def set_up_conf(self):
        """ Checks configuration and sets values to default if they're missing. """

        if "stage_limit" not in self.configuration:
            self.configuration['stage_limit'] = 80
        if "channel_run_limit" not in self.configuration:
            self.configuration['channel_run_limit'] = 20
        if "run_limit" not in self.configuration:
            self.configuration['run_limit'] = 10000
        if "burst_stages" not in self.configuration:
            self.configuration['burst_stages'] = []
        

    def activate_gm(self):
        """ Activates and shifts focus to game window. """

        window = gw.getWindowsWithTitle("MapleStory")
        if window:
            window = window[0]
            # If window is minimized, maximize it.
            if (window.isMinimized):
                window.maximize()
            # If window is not active, activate it.
            if not window.isActive:
                window.activate()
            
            # Resizing window and moving it to optimal location
            window.resizeTo(1368, 768)
            window.moveTo(0,0)
            global MAPLE_REGION
            # Setting region constraints
            MAPLE_REGION = (window.left, window.top, window.width, window.height)
            return True
        else:
            self.log("Game window not found.", "error")
            return False

    def do_dojo_run(self):
        """ Handles main logic of botting run. """

        self.log("Beginning botting actions.", "info")
        monster_has_been_alive = False
        stage_timer = 0
        try:
            while current_stage <= self.configuration['stage_limit'] + 1:
                time.sleep(0.75)
                self.detect_current_stage()
                if current_stage > 0 and current_stage < self.configuration['stage_limit'] + 1:
                    # If previous stage number is lower than current stage, 
                    # then player is probably in new map.
                    if prev_stage < current_stage:
                        self.log("Detected a new stage.", "debug")
                        # Setting stage timer as epoch current time
                        stage_timer = time.time()
                        self.walk_to_attack_position()
                        monster_has_been_alive = False
                    else:
                        global player_alive
                        monster_alive = self.monster_is_alive()
                        if monster_alive and current_stage > 0 and player_alive:
                            # Monster is alive
                            monster_has_been_alive = True
                            self.log("Attacking monster.", "debug")
                            attack_counter = 0
                            # When monster is alive, player should attack it.
                            while(monster_alive):
                                self.perform_basic_attack()
                                attack_counter += 1
                                # Check if monster is alive.
                                monster_alive = self.monster_is_alive()
                                # Every 2 iterations, check if hp has decreased.
                                if attack_counter % 2 == 0:
                                    monster_not_hit = pg.locateOnScreen('images/hp_timestamp.png', region=(MONSTER_HP_REGION))
                                    # If previous timestamp matches the hp of boss, then it hasn't lost any health.
                                    if monster_not_hit:
                                        self.log("Monster hasn't been hit for 2 iterations!", "debug")
                                        # If character is dead, break attack loop.
                                        if self.check_death_dialog():
                                            player_alive = False
                                            break
                                        # Repositioning character and continuing attack cycle.
                                        self.rotate_character()
                                # If monster hasn't been hit for 4 iterations, check stage.
                                if attack_counter % 4 == 0 and self.detect_current_stage() == -2:
                                    break
                                if monster_alive:
                                    # Take screenshot of monster hp bar.
                                    pg.screenshot('images/hp_timestamp.png', region=(MONSTER_HP_REGION))
                        elif monster_has_been_alive and player_alive and not monster_alive:
                                # Monster has been alive, but now it's killed.
                                self.log("Proceeding to portal.", "debug")
                                if self.check_death_dialog():
                                    player_alive = False
                                self.proceed_to_next_stage()
                                self.calculate_optimal_stage()

                        elif not monster_has_been_alive and player_alive and not monster_alive:
                            self.log("Checking stage timer.", "info")
                            elapsed_time = time.time() - stage_timer
                            # If 3 seconds has passed, then we can determine that the monster won't spawn bc it's killed.
                            if elapsed_time > 3:
                                monster_has_been_alive = True
                                self.proceed_to_next_stage()
                            
                elif current_stage == self.configuration['stage_limit'] + 1:
                    self.log("Maximum stage reached. Exiting run!", "info")
                    self.exit_dojo_run()
                elif current_stage == 0:
                    # We are in buff zone.
                    search_count = 0
                    while not self.find_monster_hp_bar_coords():
                        search_count += 1
                        if search_count > 10:
                            self.log("Monster HP bar not found. Stopping bot.", "info")
                            self.stop_bot()
                    self.start_timer()
                    self.buff_character()
                    self.proceed_to_next_stage()
                elif current_stage == -1:
                    # Only incrementing run count, if bot had reached end.
                    if self.run_stats['reached_end'] == True:
                        # Incrementing total run count and channel specific run count
                        self.run_stats['run_count'] += 1
                        self.run_stats['channel_run_count'] += 1
                        # Updating stats to GUI
                        self.gui.update_stats("Run count", self.run_stats['run_count'])
                        self.gui.update_stats("Channel run count", self.run_stats['channel_run_count'])
                        # Turning flag variable
                        self.run_stats['reached_end'] = False
                    # If run limit is lower or equal to run count, bot needs to be stopped.
                    if self.configuration['run_limit'] <= self.run_stats['run_count']:
                        self.log("Run limit reached. Stopping bot.", "info")
                        self.stop_bot()
                    # If channel unique run limit has been met, channel change is to be performed.
                    elif self.configuration['channel_run_limit'] <= self.run_stats['channel_run_count']:
                        self.log("Channel run limit reached.", "info")
                        self.change_channel()
                    else:
                        self.log("Starting a run.", "info")
                        self.go_to_dojo()
                elif current_stage == -2:
                    # If bot hasn't reached end already, continue.
                    if self.run_stats['reached_end'] == False:
                        self.log("Run has ended.", "debug")
                        run_time = self.get_run_time()
                        if run_time != 0 and player_alive:
                            self.run_stats['all_run_times'].append(run_time)
                            # Calculating average run time
                            avg_run_time = calculate_average_run_time(self.run_stats['all_run_times'])
                            # Updating run times and estimated points per hour to GUI
                            self.gui.update_stats("Average run time", str(avg_run_time))
                            self.gui.update_stats("Estimated pp/h", calculate_pph(avg_run_time, self.configuration['stage_limit']))
                            self.gui.update_stats("Best run time", str(min(self.run_stats['all_run_times'])))
                            self.gui.update_stats("Last run time", str(run_time))
                        # Marking the run finished.
                        self.run_stats['reached_end'] = True
                        self.close_result_dialog()
                        self.proceed_to_next_stage(True)
            
        except KeyboardInterrupt:
            sys.exit(0)

    def start_timer(self):
        """ Starts timing the run duration. """
        global start_time
        start_time = time.time()

    def get_run_time(self):
        """ Stops timing the run. """
        end_time = time.time()
        run_time = round(end_time - start_time)
        formatted_time = datetime.timedelta(seconds=run_time)
        # If run duration is more than 1 hour, then it's an erronous value.
        if formatted_time > datetime.timedelta(hours = 1):
            self.log("Run time cannot be calculated.", "info")
            return 0
        else:
            return formatted_time

    def calculate_optimal_stage(self):
        """ Calculates optimal stage limit based on current stage and current time. """

        # Getting run time after every stage
        run_time = self.get_run_time()
        if run_time != 0:
            current_pph = calculate_pph(run_time, current_stage)
            if current_pph > self.run_stats['highest_pph']:
                # Setting current pph as the highest pph achieved
                self.run_stats['highest_pph'] = current_pph
                gui_text = str(current_stage + 1) + " (" + str(current_pph) + ")"
                # Updating to gui
                self.gui.update_stats("Sugg. exit stage", gui_text)
        else:
            logger.info("Cannot calculate pph for current stage.")


    def reset_run(self):
        """ Resets some important variables when run has ended. """

        global player_alive
        global prev_attack_direction
        global current_stage
        global prev_stage
        self.run_stats['bursted_stages'] = []
        prev_attack_direction = ""
        player_alive = True
        current_stage = -3
        prev_stage = -3

    def go_to_dojo(self):
        """ Talks to lobby npc and proceeds to dojo. """
        
        dojo_npc = pg.locateOnScreen('images/lobby_npc.png', confidence=0.9, region=MAPLE_REGION)
        if dojo_npc:
            self.log("Dojo NPC found.", "info")
            time.sleep(1) 
            # Use potions.
            for key in self.configuration['potion_keys']:
                pd.press(key)
                time.sleep(0.5)
            npc_coords = pg.center(dojo_npc)
            pg.click(npc_coords)
            time.sleep(0.5)
            pd.press('down')
            time.sleep(0.5)
            pd.press('enter', presses=4, interval=1)
            # Checking if dojo is occupied (someone is already inside)
            if self.is_dojo_occupied():
                # Performing channel change
                self.change_channel()
            else:
                # Reset run
                self.reset_run()
        else:
            self.log("Dojo NPC couldn't be found.", "debug")
            # Moving mouse out of the way
            self.sync_mouse()
            self.run_stats['npc_not_found_count'] += 1
            # Changing channels after 4 failed attempts.
            if self.run_stats['npc_not_found_count'] >= 4:
                self.change_channel()
                self.run_stats['npc_not_found_count'] = 0

    def buff_character(self):
        """ Buffs up before dojo run. """

        for buff in self.configuration['buff_keys']:
            pd.press(buff)
            time.sleep(1)

    def is_dojo_occupied(self):
        """ Checks if someone is already inside dojo. """

        # Locating dialog, which tells if player is inside dojo.
        player_inside = pg.locateOnScreen('images/occupied_dojo.png', confidence=0.9, region=MAPLE_REGION)
        if player_inside:
            self.log("Dojo is occupied.", "info")
            return True
        else:
            self.log("Dojo is not occupied.", "info")
            return False

    def change_channel(self):
        """ Changes channel. """

        global SETTINGS_BTN_LOC
        # Closing dialog first
        pg.press("escape", presses=1)
        # If location of settings button has not been set yet, use img. detection to find it once.
        if SETTINGS_BTN_LOC == None:
            self.log("Detecting settings button.", "info")
            # Finding settings button location
            settings_button = pg.locateOnScreen('images/settings_btn.png', confidence = 0.9, region=MAPLE_REGION)
            # If button was found, set constant value as the center of the button.
            if settings_button:
                self.log("Settings button location saved.", "info")
                SETTINGS_BTN_LOC = pg.center(settings_button)

        # If settings button location is known, continue.
        if SETTINGS_BTN_LOC:
            # Getting centered point and clicking the button
            pg.click(SETTINGS_BTN_LOC)
            self.log("Changing channels.", "info")
            pg.press("Enter")
            time.sleep(0.5)
            channel_skip = 1
            # Maximum channel is 10
            if self.run_stats['current_channel'] == 10:
                # Decrementing channels randomly from 1 to 9.
                channel_skip = random.randint(1,9)
                # Navigating channel menu
                pg.press("Left", presses=channel_skip, interval = 0.5)
                self.run_stats['current_channel'] -= channel_skip
            else:
                self.run_stats['current_channel'] += 1
                pg.press("Right", presses=channel_skip, interval=0.5)
            # Joining channel by pressing enter
            pg.press("Enter")
            time.sleep(2.5)
            # Reseting channel run count.
            self.run_stats['channel_run_count'] = 0
            # Updating statistics.
            self.gui.update_stats("Channel run count", 0)
            self.gui.update_stats("Current channel", self.run_stats['current_channel'])
        else:
            self.log("Settings button not found. Retrying shortly.", "info")
            # Moving mouse out of the way
            self.sync_mouse()


    def exit_dojo_run(self):
        """ Exits the dojo run at maximum stage after killing the monster. """

        exit_npc = pg.locateOnScreen('images/exit_npc.png', confidence=0.9, region=MAPLE_REGION)
        if exit_npc:
            # Getting centered location coords
            npc_coords = pg.center(exit_npc)
            # Opening dialog
            pg.click(npc_coords)
            time.sleep(0.5)
            # Focusing "Yes" button
            pd.press('right')
            time.sleep(0.2)
            # Exiting dojo
            pd.press('enter')
        else:
            self.log("Can't locate exit npc.", "warning")
            # Moving mouse out of the way if that is the issue
            self.sync_mouse()

    def walk_to_attack_position(self):
        """ Walks a bit forward in the beginning of each stage. """

        pd.keyDown('right')
        # Jump randomly twice
        if random.getrandbits(1):
            pd.press('alt', presses=1)
        # Hold walk button for a random amount of time.
        time.sleep(round(random.uniform(0.5, 0.9),2))
        pd.keyUp('right')

    def close_result_dialog(self):
        """ Closes dialog that is displayed after run. """

        exit_button = pg.locateOnScreen('images/exit_results_button.png', region=MAPLE_REGION)
        # If exit button was found
        if exit_button:
            # Find center coordinates to button
            button_coords = pg.center(exit_button)
            # Click button
            pg.click(button_coords)

    def monster_is_alive(self):
        """ Checks if monster HP bar is found. """
        if MONSTER_HP_REGION != ():
            monster_hp_bar = pg.locateOnScreen("images/monster_hp_bar.png", region=MONSTER_HP_REGION)
            if monster_hp_bar:
                # If hp bar matched an empty hp bar, then the monster is dead as dead fish.
                return False
            else:
                # If match wasn't found, then monster still has hp.
                return True
        else:
            logger.info("Finding monster hp bar coords again.")
            # Run had been started later than 0 stage, so region had not been initialized.
            # Doing it now.
            self.find_monster_hp_bar_coords()

    def proceed_to_next_stage(self, exit_stage=False):
        """ Transports player to next level. """
        # Turn right
        pd.press("right", presses = 2)
        # Perform teleport to right corner.
        with pg.hold('right'):
            pd.press('c', presses = 3, interval = 0.8)

        pd.keyDown('left')
        if exit_stage:
            # Portal at exit stage is at a different location
            time.sleep(self.configuration['exit_walk'])
        else:
            time.sleep(self.configuration['stage_walk'])
        pd.keyUp('left')
        pd.press('up', presses=2)

        # Reset attack position
        global prev_attack_direction
        prev_attack_direction = ''
        time.sleep(0.5)

    def rotate_character(self):
        """ Repositions the character and finds the monster """

        global prev_attack_direction
        direction = 'right'
        if prev_attack_direction == 'right':
            direction = 'left'
        
        prev_attack_direction = direction
        pg.keyDown(direction)
        time.sleep(random.uniform(0.08, 0.6))
        pg.keyUp(direction)

    def find_monster_hp_bar_coords(self):
        """ Finds monster hp bar coordinates. """
        try:
            monster_tag = pg.locateOnScreen("images/monster_tag.png", region=MAPLE_REGION)
            if monster_tag:
                global MONSTER_HP_REGION
                # Setting monster hp bar region based on monster tag
                MONSTER_HP_REGION = (monster_tag.left - 190, monster_tag.top - 28, 315, 21)
                if not os.path.isfile("images/monster_hp_bar.png"):
                    pg.screenshot("images/monster_hp_bar.png", region=MONSTER_HP_REGION)
                return True
            else:
                return False
        except OSError:
            self.log("Monster tag image is missing.", "error")
            return False
    
    def perform_basic_attack(self):
        """ Performs attack.  """
        # If stage is hard, use burst first.
        if current_stage in self.configuration['burst_stages'] and current_stage not in self.run_stats['bursted_stages']:
            logger.info("Performing burst attack.")
            # Using burst buffs, if given.
            if 'burst_buff_keys' in self.configuration:
                # Iterating over buff keys and pressing them one at a time.
                for key in self.configuration['burst_buff_keys']:
                    pd.press(key)
                    time.sleep(0.8)
            if self.configuration['burst_att_type'] == "Press once":
                pd.press(self.configuration['burst_att_key'])
            elif self.configuration['burst_att_type'] == 'Hold':
                pd.keyDown(self.configuration['burst_att_key'])
                time.sleep(self.configuration['burst_dur'])
                pd.keyUp(self.configuration['burst_att_key'])
            else:
                pd.press(self.configuration['burst_att_key'],
                         presses = self.configuration['burst_dur'],
                         interval=1)
            self.run_stats['bursted_stages'].append(current_stage)
            # Returning true instead of attacking, since monster is probs dead.
            return True

        # Normal attack with the user chosen mode
        if self.configuration['main_att_type'] == 'Hold':
            # If attacking has to be done to both directions, split duration.
            if self.configuration['both_directions'] == True:
                # Splitting duration in half
                duration = round(self.configuration['main_dur'] / 2)
                self.hold_attack('right', duration, self.configuration['main_att_key'])
                self.hold_attack('left', duration, self.configuration['main_att_key'])
                # Turning back right
                pd.press('right')
            else:
                # Attacking right for the whole duration
                self.hold_attack('right', self.configuration['main_dur'], self.configuration['main_att_key'])
        else:
            # Attacking right first
            self.press_attack('right', self.configuration['main_att_key'])
            if self.configuration['both_directions'] == True:
                # Attacking left if needed
                self.press_attack('left', self.configuration['main_att_key'])
                # Turn to right again.
                pd.press('right')


    def hold_attack(self, direction, duration, key):
        ''' Attacks to given direction by holding down the attack key for given duration. '''

        pd.press(direction)
        pd.keyDown(key)
        time.sleep(duration)
        pd.keyUp(key)

    def press_attack(self, direction, key):
        ''' Attacks to the given direction by pressing the attack repeatedly. '''

        pd.press(direction)
        pd.press(key, presses=3, interval=0.2)

    def check_death_dialog(self):
        """ Checks if death dialog is displayed in case character dies. """

        dd = pg.locateOnScreen('images/death_dialog.png', region=MAPLE_REGION)
        if dd:
            # Character is dead
            dd_coords = pg.center(dd)
            # Clicking OK button to respawn.
            pg.click(dd_coords)
            self.run_stats['death_count'] += 1
            self.gui.update_stats("Death count", self.run_stats['death_count'])
            return True
        else:
            return False


    def take_screenshot(self):
        """ Takes a screenshot of map name. """
        image_name = self.gui.generate_stage_image_name()
        pg.screenshot("images/" + image_name, region = MAP_NAME_REGION)
        # This is used to take any needed images from maple region.
        pg.screenshot("images/temp.png", region = MAPLE_REGION)
        self.gui.show_stage_image()

    def detect_map_name_bar(self):
        """ Detects where the map name bar is located and calculates optimal region coords."""
        
        self.log("Detecting map name bar world button.", "debug")
        try:
            wb = pg.locateOnScreen("images/world_btn.png", confidence=0.9, region=MAPLE_REGION)
            name_bar_width = 260
            if wb:
                self.log("Minimap location found.", "debug")
                global MAP_NAME_REGION
                MAP_NAME_REGION = (0, wb.top - 1, name_bar_width - wb.width, wb.height + 1)
                return True
            else:
                self.log("Could not find world button.", "debug")
                self.sync_mouse()
                return False
        except ValueError:
            return False

    def detect_current_stage(self):
        """ Detects which stage player is in. """

        try:
            # Iterate through every stage
            self.log("Detecting current stage...", "debug")
            for stage in range(-2, self.configuration['stage_limit'] + 2):
                if pg.locateOnScreen('images/stage_' + str(stage) + '.png', grayscale=True, region = MAP_NAME_REGION):
                    logger.info("Detected stage: " + str(stage))
                    self.gui.update_stats("Current stage", stage)
                    global current_stage
                    global prev_stage
                    prev_stage = current_stage
                    # Set global var to mark the stage.
                    current_stage = stage
                    return stage
        except Exception as ex:
            self.log(ex, "debug")

    def run(self):
        # Activating game window
        activated = self.activate_gm()
        if activated:
            self.log("Game window activated.", "info")
            # Detecting map name bar to update region coordinates.
            name_bar_found = self.detect_map_name_bar()
            self.gui.update_status(name_bar_found)
            # If name bar was not found, loop until it is found.
            while not name_bar_found:
                time.sleep(2)
                name_bar_found = self.detect_map_name_bar()

            if name_bar_found:
                # If screenshot mode is not on, do normal run.
                if not self.sc_mode:
                    # Start bot main logic
                    self.do_dojo_run()
                else:
                    self.log("Taking a screenshot.", "info")
                    self.take_screenshot()
                    self.stop_bot()
            else:
                self.stop_bot()
                    
    def sync_mouse(self):
        """ Moves mouse cursor into a place where it is not in front of any item. """

        pg.moveTo(MAPLE_REGION[0] + 15, MAPLE_REGION[1] + 15)

    def log(self, msg, msg_type):
        """ Logs message to command line and GUI. """

        if msg_type == "info":
            logger.info(msg)
        elif msg_type == "warning":
            logger.warning(msg)
        elif msg_type == "debug":
            logger.debug(msg)
        else:
            logger.error(msg)
        self.gui.update_status(msg)

    def stop_bot(self):
        self.log("Bot has stopped.", "info")
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')

  
    def get_id(self):
 
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

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
from helper_constants import STAGE_NAMES
from logzero import logger

# Tuple for setting the region where map name should be detected from.
# Values are left, top, width, height in order.
MAP_NAME_REGION = (0, 30, 320, 35)
# Maple window region
MAPLE_REGION = ()
MONSTER_HP_REGION = ()
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
                self.run_stats = {'reached_end': False, 'run_count': 0}
                
    def set_up_conf(self):
        """ Checks configuration and sets values to default if they're missing. """

        if "stage_limit" not in self.configuration:
            self.configuration['stage_limit'] = 80
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
        try:
            while current_stage <= self.configuration['stage_limit'] + 1:
                time.sleep(0.75)
                self.detect_current_stage()
                if current_stage > 0 and current_stage < self.configuration['stage_limit'] + 1:
                    # If previous stage number is lower than current stage, 
                    # then player is probably in new map.
                    if prev_stage < current_stage:
                        self.log("Detected a new stage.", "debug")
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
                                self.perform_basic_attack(1.2)
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
                        self.run_stats['run_count'] += 1
                        self.run_stats['reached_end'] = False
                    # If run limit is lower or equal to run count, bot needs to be stopped.
                    if self.configuration['run_limit'] <= self.run_stats['run_count']:
                        self.log("Run limit reached. Stopping bot.", "info")
                        self.stop_bot()
                    else:
                        self.log("Starting a run.", "info")
                        self.go_to_dojo()
                elif current_stage == -2:
                    # If bot hasn't reached end already, continue.
                    if self.run_stats['reached_end'] == False:
                        self.log("Run has ended.", "debug")
                        run_time = self.get_run_time()
                        if run_time != 0:
                            self.log("Run duration was: " + str(run_time), "info")
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

    def reset_run(self):
        """ Resets some important variables when run has ended. """

        global player_alive
        global prev_attack_direction
        global current_stage
        global prev_stage
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
            # Reset run
            self.reset_run()
        else:
            self.log("Dojo NPC couldn't be found.", "debug")

    def buff_character(self):
        """ Buffs up before dojo run. """

        for buff in self.configuration['buff_keys']:
            pd.press(buff)
            time.sleep(1.5)


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

        monster_hp_bar = pg.locateOnScreen("images/monster_hp_bar.png", region=MONSTER_HP_REGION)
        if monster_hp_bar:
            # If hp bar matched an empty hp bar, then the monster is dead as dead fish.
            return False
        else:
            # If match wasn't found, then monster still has hp.
            return True

    def proceed_to_next_stage(self, exit_stage=False):
        """ Transports player to next level. """

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
    
    def perform_basic_attack(self, duration):
        """ Performs attack.  """

        # If stage is hard, use burst first.
        if current_stage in self.configuration['burst_stages']:
            # Using burst buffs, if given.
            if 'burst_buff_keys' in self.configuration:
                pd.press(self.configuration['burst_buff_keys'], interval=1)
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
            # Returning true instead of attacking, since monster is probs dead.
            return True
        # Normal attack with the user chosen mode
        if self.configuration['main_att_type'] == 'Hold':
            pd.press('right')
            pd.keyDown(self.configuration['main_att_key'])
            time.sleep(round(self.configuration['main_dur'] / 2))
            pd.keyUp(self.configuration['main_att_key'])

            pd.press('left')
            pd.keyDown(self.configuration['main_att_key'])
            time.sleep(round(self.configuration['main_dur'] / 2))
            pd.keyUp(self.configuration['main_att_key'])
        else:
            pd.press(self.configuration['main_att_key'], presses=5)
            time.sleep(0.4)
            pd.press('left')
            pd.press(self.configuration['main_att_key'], presses=5)
            time.sleep(0.4)
            pd.press('right')

    def check_death_dialog(self):
        """ Checks if death dialog is displayed in case character dies. """

        dd = pg.locateOnScreen('images/death_dialog.png', region=MAPLE_REGION)
        if dd:
            # Character is dead
            dd_coords = pg.center(dd)
            # Clicking OK button to respawn.
            pg.click(dd_coords)
            return True
        else:
            return False

    def take_screenshot(self):
        """ Takes a screenshot of map name. """
        image_name = self.gui.generate_stage_image_name()
        pg.screenshot("images/" + image_name, region = MAP_NAME_REGION)
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
                    self.log("Detected stage: " + str(stage), "debug")
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

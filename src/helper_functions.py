import datetime

KEY_LIST = ['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
'8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
'browserback', 'browserfavorites', 'browserforward', 'browserhome',
'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
'command', 'option', 'optionleft', 'optionright']

SCREENSHOT_GUIDE_TEXT = "To detect a map, a screenshot of minimap name has to be taken for each map. Choose the current map you're in and press 'Take screenshot' button to take the image. Repeat this action for every stage you want to bot at, including lobby, buff stage and exit stages."

STAGE_NAMES = ['Dojo lobby', 'Buff stage', 'Exit stage', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', 'Exit stage']

IMAGE_NAMES = ['exit_npc', 'lobby_npc','monster_tag', 'death_dialog', 'exit_results_button', 'world_btn', 'settings_btn', 'occupied_dojo']

STATISTICS_COLUMNS = {"Run count": 0, "Channel run count": 1,
                      "Death count": 2, "Average run time": 3,
                      "Last run time": 4,"Best run time": 5,
                      "Estimated pp/h": 6, "Sugg. exit stage": 7,
                      "Current channel": 8, "Current stage": 9}

# Point accumulation up to stage 25
STAGE_POINTS = [10, 20, 30, 40, 50, 60, 70,
                80, 90, 190, 210, 230, 250,
                270, 290, 310, 330, 350, 370,
                570, 610, 650, 690, 730, 770]

def calculate_pph(avg_run_time, stage_limit):
    """ Calculates the estimated points per hour. """

    # Calculating how many times dojo can be run in an hour with the current speed
    runs_per_hour = datetime.timedelta(hours=1) / avg_run_time
    # Calculating the amount of points that the bot should be able to generate in an hour
    points_per_hour = int(runs_per_hour * STAGE_POINTS[stage_limit - 1])
    return points_per_hour


def calculate_average_run_time(run_times):
        """ Calculates average run time when given list of run times. """

        # Calculating average run time out of a list of all run times.
        avg_time = sum(run_times, datetime.timedelta(0)) / len(run_times)
        # Trimming out microseconds.
        trimmed_time = avg_time - datetime.timedelta(microseconds=avg_time.microseconds)
        return trimmed_time
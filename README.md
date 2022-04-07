# Maplestory Dojo Bot
A botting program for a game called Maplestory. Bot includes an interactive GUI and it does not require any user actions once it has been set up properly.

This bot is made to be used in the Mu Lung Dojo content and it does not work anywhere else.
Maplestory version for which this bot was developed and tested on is v231.1, but it could work on older or newer versions.

GUI is created with Python GUI library tkInter and the actual bot utilizes automation libraries such as PyDirectInput and PyAutoGui.
Program can be compiled into an executable by using ex. auto-py-to-exe library or py-installer.


You can compile this program to receive an EXE-file for easier use.
Execute the command below in the root directory of this project (Replace the "\<PATH TO ROOT DIR\>" with the your own paths.)
The path should look something like this: "C:/Users/User/Documents/Maplestory-Dojo-Bot/src/\<FILE NAME\>"

```console
pyinstaller --noconfirm --onedir --windowed --icon "<PATH TO ROOT DIR>/icon-png.ico" --uac-admin --add-data "<PATH TO ROOT DIR>/blurrybg.png;." --add-data "<PATH TO ROOT DIR>/icon-png.ico;." --add-data "<PATH TO ROOT DIR>/MapleCursor.ani;." --add-data "<PATH TO ROOT DIR>/MapleCursor_Link.ani;." --add-data "<PATH TO ROOT DIR>/src/dojobot.py;." --add-data "<PATH TO ROOT DIR>/src/helper_functions.py;."  "<PATH TO ROOT DIR>/src/dojobot_gui.py"
```


# Screenshots of GUI
## Main tab
<img style="height:60%;width:60%" src="https://i.imgur.com/z0NqwSe.png" alt="Screenshot of Bot graphical user interface (Main tab is shown)">

## Settings tab
<img style="height:60%;width:60%" src="https://i.imgur.com/lhMaWTA.png" alt="Screenshot of Bot graphical user interface (Settings tab is shown)">

## Miscellaneous tab
<img style="height:60%;width:60%" src="https://i.imgur.com/j4fBpbY.png" alt="Screenshot of Bot graphical user interface (Misc tab is shown)">

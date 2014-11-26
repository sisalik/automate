*This readme is incomplete. More information to be added soon.*

automate
========
automate is a Windows application launcher written in Python. Its main purpose is to make it quick and easy to launch anything - from Start menu items to websites and scripts. It is easily extendable and customizable.

<img src="http://i.imgur.com/rEl6ycP.png" />

Dependencies
========
- Python 2.7.x
- PyQt4
- Python for Windows Extensions

Getting started
========
Install the dependencies and run automate.pyw. Hold down the caps lock key and start typing a command. Release caps lock to execute.

Some commands, such as `Switch to...` or `Google...` expect parameters (window title, search string etc.). Press the tab key when these commands are selected to enter the command's submenu.

Customization
========
Configuration is loaded from config/config.json. Colour schemes and other styles for the windows can be loaded from .css files, stored in the same directory.

Any .py files in the `commands` folder will be automatically imported as command files. You can register text commands or hotkeys in those files. Some examples have been provided.

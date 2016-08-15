*This is alpha software. You will most likely see some bugs. Please use the issue tracker to report them, along with any feature suggestions! :)*

automate
========
automate is a Windows application launcher written in Python. Its main purpose is to make it quick and easy to launch anything - from Start menu items to websites and scripts. It is easily extendable and customizable, including CSS theme support and Python plugins.

<img src="http://i.imgur.com/l5rekZV.png" />
<img src="http://i.imgur.com/DdWoMVr.png" />

Dependencies
========
- Python 2.7.x
- PyQt4
- Python for Windows Extensions

Usage
========
Install the dependencies and run automate.pyw. Hold down the `CAPS LOCK` key and start typing a command -- try out some of the ones mentioned below. Release `CAPS LOCK` to execute. Use the `Exit` command or right click on the system tray icon to stop the program.

Automatic shortcut discovery
--------
By default, all Start menu shortcuts and Control Panel items are available as commands. Try out some of these: `Notepad`, `Paint`, `Control Panel`, `Programs and Features`.

User shortcuts
--------
You can also add your own commands. Highlight a URL, a file or a folder and use the command `Create shortcut...`. Type a name for your shortcut and automate will retrieve the location of your selection and add it as a new command. To remove a shortcut, use `Remove shortcut...`.

Built-in Google search
--------
Double-pressing `CAPS LOCK` will allow you to perform a quick Google search.

More commands
--------
Some more built-in commands include: `Google...`, `Switch to...`, `Close...`, `Screen off`, `Sleep`, `Hibernate`. Some of these, such as `Switch to...` or `Google...` expect arguments (window title, search string etc.). Press the `TAB` key when these commands are selected to enter the command's submenu.

When automate doesn't recognise a command, it will try to execute it using the same mechanism as the Run dialog in Windows. Try: `msconfig`, `regedit`, `google.com`.

File system navigation
--------
You can also use automate as a quick file explorer. When you start typing a directory name, such as `C:\`, automate will list the contents as autocomplete suggestions. Press `TAB` to trigger autocompletion and `ESC` to move back to the parent directory.

If a user shortcut points to a file or a folder, then pressing `TAB` will expand the path and you will be able to navigate from there.

Customization
========
Configuration is loaded from config/config.json. Colour schemes and other styles for the windows can be loaded from .css files, stored in the same directory.

Any .py files in the `commands` folder will be automatically imported as command files. You can register text commands or hotkeys in those files. Some examples have been provided.

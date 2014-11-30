import json

from PyQt4 import QtCore, QtGui

from message import message
from command_handler import CommandHandler
from input_hook import send_combo


def load_shortcuts():
    """Load the shortcuts dictionary from the JSON file."""
    with open("config/shortcuts.json") as shortcuts_file:
        try:
            return json.load(shortcuts_file, "utf-8")  # Load existing shortcut dictionary
        except ValueError:  # No shortcuts saved in the file
            return {}


def save_shortcuts(dictionary):
    """Save a dictionary into the shortcuts JSON file."""
    with open("config/shortcuts.json", "w") as shortcuts_file:
        shortcuts_file.write(json.dumps(dictionary, sort_keys=True, indent=4, ensure_ascii=False).encode("utf-8"))


@CommandHandler.register("Create shortcut...", args=[""], subcmds=True)
def create_shortcut(name=None):
    if name is None:  # Register subcommands
        return []
    elif name == "":
        message("Press tab to enter a name for the shortcut first", "Error")
    else:
        # Wait for the command window to fade out
        CommandHandler.main_gui.after_hide = lambda name=name: get_shortcut(name)


def get_shortcut(name):
    clipboard = QtGui.QApplication.clipboard()
    old_formats = list(clipboard.mimeData().formats())
    old_clipboard = QtCore.QMimeData()
    for f in old_formats:
        data = clipboard.mimeData().data(f)
        old_clipboard.setData(f, data)

    clipboard.dataChanged.connect(lambda n=name, old_cb=old_clipboard: register_shortcut(n, old_cb))
    send_combo("LCONTROL + C")  # Send the ctrl+v key combination to copy active selection (file or text)


def register_shortcut(name, old_clipboard):
    clipboard = QtGui.QApplication.clipboard()
    clipboard.dataChanged.disconnect()

    urls = clipboard.mimeData().urls()
    text = clipboard.text()
    if list(old_clipboard.formats()):  # Check if the old clipboard MIME object contains any data
        CommandHandler.main_gui.call(clipboard.setMimeData, [old_clipboard])

    if text:  # The clipboard contains text
        shortcut = unicode(text)
    elif urls:  # The clipboard contains a file
        shortcut = unicode(urls[0].toString())[8:].replace("/", "\\")
    else:
        message("Unable to register the selection as a shortcut", "Error")
        return

    shortcuts_dict = load_shortcuts()  # Load shortcuts from the config file
    if name.decode("utf-8") not in shortcuts_dict:
        keyword = "registered"
    else:
        keyword = "updated"
        CommandHandler.remove(name)  # Delete the existing command
    CommandHandler.register(name, CommandHandler.run, [shortcut.encode("utf-8")])  # Register the new command
    shortcuts_dict.update({name.decode("utf-8"): shortcut})  # Update with new shortcut
    save_shortcuts(shortcuts_dict)  # Write back to the file
    message("Shortcut %s: [i]%s[/i]\nTarget: [i]%s[/i]" % (keyword, name.decode("utf-8"), shortcut), "Success")


@CommandHandler.register("Remove shortcut...", args=[""], subcmds=True)
def remove_shortcut(name=None):
    if name is None:  # Register subcommands
        shortcuts_dict = load_shortcuts()
        return [key.encode("utf-8") for key in shortcuts_dict]
    elif name == "":
        message("Press tab to select a shortcut to remove", "Error")
    else:
        if CommandHandler.remove(name):
            shortcuts_dict = load_shortcuts()  # Load shortcuts from the config file
            shortcuts_dict.pop(name.decode("utf-8"))  # Remove shortcut
            save_shortcuts(shortcuts_dict)  # Write back to the file
            message("Shortcut removed: [i]%s[/i]" % name.decode("utf-8"), "Success")
        else:
            message("Unable to remove shortcut: [i]%s[/i]" % name.decode("utf-8"), "Error")

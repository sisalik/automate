import json

from PyQt4 import QtCore, QtGui

from message import message
from command_handler import CommandHandler
from input_hook import send_combo


def load_shortcuts():
    """Load the shortcuts dictionary from the JSON file."""
    with open("commands/shortcuts.json") as shortcuts_file:
        try:
            return json.load(shortcuts_file, "utf-8")  # Load existing shortcut dictionary
        except ValueError:  # No shortcuts saved in the file
            return {}


def save_shortcuts(dictionary):
    """Save a dictionary into the shortcuts JSON file."""
    with open("commands/shortcuts.json", "w") as shortcuts_file:
        shortcuts_file.write(json.dumps(dictionary, sort_keys=True, indent=4, ensure_ascii=False).encode("utf-8"))


@CommandHandler.register("Create shortcut...", args=[""], subcmds=True)
def create_shortcut(name=None):
    if name is None:  # Register subcommands
        return []
    elif name == "":
        message("Press tab to enter a name for the shortcut first", "Error")
    else:
        # Call from the main thread because the function uses Qt objects
        CommandHandler.main_gui.call(get_shortcut, [name])


def get_shortcut(name):
    """Copy the selected file/text into the clipboard."""
    # Store the current clipboard contents to be restored later
    clipboard = QtGui.QApplication.clipboard()
    old_formats = list(clipboard.mimeData().formats())
    old_clipboard = QtCore.QMimeData()
    for f in old_formats:
        data = clipboard.mimeData().data(f)
        old_clipboard.setData(f, data)

    # register_selected_shortcut function to be called when a clipboard change has been detected
    clipboard.dataChanged.connect(lambda n=name, old_cb=old_clipboard: register_selected_shortcut(n, old_cb))
    clipboard_timer.start()
    send_combo("LCONTROL + C")  # Send the ctrl+v key combination to copy active selection (file or text)


def register_selected_shortcut(name, old_clipboard):
    """Retrieve the text/filename from the clipboard and register it as a new command."""
    clipboard = QtGui.QApplication.clipboard()
    clipboard.dataChanged.disconnect()
    clipboard_timer.stop()

    urls = clipboard.mimeData().urls()
    text = clipboard.text()
    if list(old_clipboard.formats()):  # Check if the old clipboard MIME object contains any data
        CommandHandler.main_gui.call(clipboard.setMimeData, [old_clipboard])  # Restore the old clipboard contents

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
    register_shortcut(name, shortcut)  # Register the new command
    shortcuts_dict.update({name.decode("utf-8"): shortcut})  # Update with new shortcut
    save_shortcuts(shortcuts_dict)  # Write back to the file
    message("Shortcut %s: [i]%s[/i]\nTarget: [i]%s[/i]" % (keyword, name.decode("utf-8"), shortcut), "Success")


def register_shortcut(name, path):
    CommandHandler.register(name.encode("utf-8"), CommandHandler.run, [path.encode("utf-8")])


def no_data_copied():
    clipboard_timer.stop()
    QtGui.QApplication.clipboard().dataChanged.disconnect()
    message("Unable to retrieve clipboard data. Select a file or some text and try again.", "Error")


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


# On import, register all the shortcuts
try:
    shortcuts_dict = load_shortcuts()
except ValueError:  # No shortcuts saved in the file
    pass
else:
    for k, v in shortcuts_dict.items():
        register_shortcut(k, v)

clipboard_timer = QtCore.QTimer()
clipboard_timer.timeout.connect(no_data_copied)
clipboard_timer.setInterval(2000)

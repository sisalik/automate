import time
import json
import os
import sys

from PyQt4 import QtCore, QtGui

from input_hook import Hook, send_combo
from command_handler import CommandHandler
import message
from tip_box import TipBox


class CommandWindow(QtGui.QWidget):
    """Main command window class. Contains a QLineEdit for command entry and an autocomplete suggestion list.
    Also serves as the main widget for the QApplication.
    """

    message_signal = QtCore.pyqtSignal(str, str, int)  # Signal to show message boxes
    call_signal = QtCore.pyqtSignal(object, object)  # Signal to call functions from the main GUI thread

    def __init__(self, parent=None):
        flags = QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        super(CommandWindow, self).__init__(parent, flags)

        self.load_config()
        self.init_window()
        self.init_tray_icon()
        self.init_widgets()
        self.init_anim()

    def load_config(self):
        # Load configuration file
        with open("config/config.json") as config_file:
            # Strip comments (lines that contain //)
            stripped = "".join([line for line in config_file if "//" not in line])
        config = json.loads(stripped)
        for k, v in config.items():
            setattr(self, k, v)

        # Load the stylesheet for the window
        with open("config/" + self.theme) as css_file:
            self.setStyleSheet(css_file.read())

        # Load shortcuts
        with open("config/shortcuts.json") as shortcuts_file:
            try:
                shortcuts_dict = json.load(shortcuts_file, "utf-8")
            except ValueError:  # No shortcuts saved in the file
                pass
            else:
                for k, v in shortcuts_dict.items():
                    CommandHandler.register(k.encode("utf-8"), CommandHandler.run, [v.encode("utf-8")])

        # Set up a timer to watch the files for changes, restarting the script if detected
        # Solution idea from Petr Zemek (http://blog.petrzemek.net/2014/03/23/restarting-a-python-script-within-itself/)
        watched_files = [__file__, "config/config.json", "config/" + self.theme]
        self.watched_files_mtimes = [(f, os.path.getmtime(f)) for f in watched_files]
        self.watch_timer = QtCore.QTimer()
        self.watch_timer.timeout.connect(self.check_files)
        self.watch_timer.start(1000)  # Check every second

    def init_window(self):
        # Set up the window
        self.resize(*self.default_size)
        self.setWindowOpacity(self.default_alpha)

        # Set up the message widget
        message.Message.main_gui = self
        message.Message.default_alpha = self.default_alpha  # Default window transparency (0..1)
        message.Message.fade_duration = self.fade_duration  # Fade animation duration (ms)
        message.Message.stylesheet = self.styleSheet()

        # Connect signals to slots
        self.message_signal.connect(self.on_message)
        self.call_signal.connect(self.on_call)

        # Initialise some attributes
        self.history = []  # Command history
        self.history_sel = 0  # History selection index
        self.last_shown = 0  # Time when the command box was last shown (s) -- for detecting double taps

    def init_widgets(self):
        # Command box (where you type the commands)
        self.cmd_box = QtGui.QLineEdit(self)
        self.cmd_box.setObjectName("cmd_box")
        self.cmd_box.textChanged.connect(self.on_change)
        self.cmd_box.setGeometry(QtCore.QRect(0, 0, *self.default_size))

        # Help text label (overlaid on top of the command box)
        self.help_text = QtGui.QLabel(parent=self)
        self.help_text.setObjectName("help_text")
        self.help_text.setGeometry(QtCore.QRect(0, 0, *self.default_size))

        # Autocomplete suggestion ('tip') list box
        self.tip_box = TipBox(self, (0, self.default_size[1]), (self.default_size[0], self.tip_row_height), self.tip_rows)

    def init_anim(self):
        # Slide animation (self.slide)
        self.expand_anim = QtCore.QPropertyAnimation(self, "size")
        self.expand_anim.setDuration(self.slide_duration)
        easing = QtCore.QEasingCurve(QtCore.QEasingCurve.OutElastic)
        easing.setPeriod(0.8)
        self.expand_anim.setEasingCurve(easing)

        self.contract_anim = QtCore.QPropertyAnimation(self, "size")
        self.contract_anim.setDuration(self.slide_duration)
        easing = QtCore.QEasingCurve(QtCore.QEasingCurve.OutQuint)
        self.contract_anim.setEasingCurve(easing)

        # Fade animation (self.fade)
        self.fade_anim = QtCore.QPropertyAnimation(self, "windowOpacity")
        self.fade_anim.setDuration(self.fade_duration)
        self.fade_anim.finished.connect(self.on_fade_finished)

    def init_tray_icon(self):
        self.tray_menu = QtGui.QMenu(self)
        quit_action = QtGui.QAction("&Quit", self, triggered=QtGui.qApp.quit)
        about_action = QtGui.QAction("&About", self, triggered=self.on_about)
        self.tray_menu.addAction(about_action)
        self.tray_menu.addAction(quit_action)

        self.tray_icon = QtGui.QSystemTrayIcon(self)
        self.tray_icon.setContextMenu(self.tray_menu)
        icon = QtGui.QIcon("res/icon1_128x128.png")
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)
        self.tray_icon.setToolTip("automate 0.1.0")
        self.tray_icon.show()

    def center(self):
        frame_geom = self.frameGeometry()
        center_point = QtGui.QDesktopWidget().screenGeometry().center()
        frame_geom.moveCenter(center_point)
        self.move(frame_geom.topLeft())

    def showEvent(self, event):
        if time.time() - self.last_shown < 0.25:  # Double tapped caps lock
            self.on_double_tap()
        self.last_shown = time.time()

        self.setWindowOpacity(self.default_alpha)
        self.show()
        self.center()
        # For a bizarre reason, it is necessary to send an Alt key press before activating the window -- otherwise it may not
        # always work! Read: http://www.shloemi.com/2012/09/solved-setforegroundwindow-win32-api-not-always-works/
        send_combo("MENU")
        self.activateWindow()
        event.accept()

    def hideEvent(self, event):
        self.on_fade_finished()
        self.after_hide()
        self.after_hide = lambda: None
        event.accept()

    def after_hide(self):
        pass

    def slide(self, height):
        if self.default_size[1] + height < self.height():
            animation = self.contract_anim
        else:
            animation = self.expand_anim

        animation.stop()
        animation.setEndValue(QtCore.QSize(self.default_size[0], self.default_size[1] + height))
        animation.start()

    def fade(self):
        self.fade_anim.setEndValue(0)
        self.fade_anim.start()

    def on_fade_finished(self):
        CommandHandler.reset_mode()  # Reset autocomplete search list to entire commands list
        self.help_text.setText("")
        self.clear()
        self.repaint()  # The previous command can sometimes flicker in the entry box upon reopening otherwise
        self.hide()

    def get_text(self):
        return unicode(self.cmd_box.text()).encode("utf-8")

    def set_text(self, text):
        self.cmd_box.setText(text)

    def clear(self):
        self.cmd_box.setText("")
        self.on_change()

    def get_command(self):
        if self.tip_box.rows > 0:
            command = self.tip_box.get_selection()
            text = self.get_text()
            if '\\' in text:  # Folder navigation mode
                command = text[:text.rfind('\\') + 1] + command
            return command
        else:
            return self.get_text()

    def run_command(self):
        command = self.get_command()
        if command:
            subcommand_mode = CommandHandler.active_command is not None
            if CommandHandler.run(command) and not subcommand_mode:
                self.history.insert(0, command)
            self.fade()
        else:
            self.hide()

    def on_change(self):
        cmd_text = self.get_text()
        if cmd_text:
            self.help_text.hide()
        else:
            self.help_text.show()
        self.ac_thread = CommandHandler.get_matches(cmd_text)
        self.ac_thread.suggestions.connect(self.on_suggestions)
        if CommandHandler.ac_delay > 0:  # If the delay is longer than 0 ms, clear the suggestions list before repopulating
            self.ac_thread.suggestions.emit([])

    def on_suggestions(self, suggestions):
        pattern = self.get_text()
        if '\\' in pattern:  # Folder navigation mode
            pattern = pattern[pattern.rfind('\\') + 1:]
        self.tip_box.set_text(suggestions, pattern)

    def on_message(self, text, title, timeout):
        self.msg = message.Message(text, title, timeout)

    def check_files(self):
        for f, mtime in self.watched_files_mtimes:
            if os.path.getmtime(f) > mtime:
                restart()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Up:
            self.on_up()
        elif e.key() == QtCore.Qt.Key_Down:
            self.on_down()
        elif e.key() == QtCore.Qt.Key_Tab:
            self.on_tab()
        elif e.key() == QtCore.Qt.Key_Escape:
            self.on_esc()

    def on_double_tap(self):
        CommandHandler.get_subcmds("Google...")
        self.help_text.setText(CommandHandler.active_command)

    def on_up(self):
        if self.tip_box.rows > 1:
            self.tip_box.up()
        elif self.history:  # A command history exists
            if not self.get_text():
                self.history_sel = 0
            elif 0 <= self.history_sel < len(self.history) - 1:
                self.history_sel += 1
            self.set_text(self.history[self.history_sel])
            self.on_change()

    def on_down(self):
        if self.tip_box.rows > 1:
            self.tip_box.down()
        elif self.history:  # A command history exists
            if not self.get_text():
                return
            elif 0 < self.history_sel < len(self.history):
                self.history_sel -= 1
                self.set_text(self.history[self.history_sel])
                self.on_change()
            elif self.history_sel == 0:
                self.clear()

    def on_tab(self):
        command = self.get_command()
        if '\\' in command:  # Folder navigation mode
            self.set_text(command + '\\')
        elif CommandHandler.get_subcmds(command):
            self.help_text.setText(CommandHandler.active_command)
            self.clear()
        else:
            self.set_text(command)
            self.on_change()

    def on_esc(self):
        text = self.get_text()
        if '\\' in text:  # Folder navigation mode
            if len(text) == 3:  # Only drive letter, e.g. C:\ or D:\
                self.set_text("")
            else:
                self.set_text(text[:text[:-1].rfind('\\', 2)] + '\\')
        elif CommandHandler.active_command:  # A subcommand is active
            CommandHandler.reset_mode()  # Reset autocomplete search target to entire commands list
            self.help_text.setText("")
        else:
            self.set_text("")
        self.on_change()

    def on_about(self):
        QtGui.QMessageBox.about(self, "About automate 0.1.0", "automate is a Windows application launcher written in Python. " +
            "Its main purpose is to make it quick and easy to launch anything -- from Start menu items " +
            "to websites and scripts. It is easily extendable and customizable.")

    def call(self, function, args=[]):
        """Call any function from the main GUI thread. This is sometimes needed because Qt doesn't allow GUI-related functions
        to be called from any other thread.

        Args:
            function: Function to be called.
            args: List or tuple of arguments to pass to the function.
        """
        self.call_signal.emit(function, args)  # Emit a signal to the main thread

    def on_call(self, function, args):
        function(*args)


@CommandHandler.register("Exit")
def exit():
    cmd_win.tray_icon.hide()
    app.exit()
    Hook.stop()


@CommandHandler.register("Reload")
def restart():
    exit()
    python = sys.executable
    os.execl(python, python, *sys.argv + ["no-splash"])


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
        message.message("Press tab to enter a name for the shortcut first", "Error")
    else:
        # Wait for the command window to fade out
        cmd_win.after_hide = lambda name=name: get_shortcut(name)


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
        cmd_win.call(clipboard.setMimeData, [old_clipboard])

    if text:  # The clipboard contains text
        shortcut = unicode(text)
    elif urls:  # The clipboard contains a file
        shortcut = unicode(urls[0].toString())[8:].replace("/", "\\")
    else:
        message.message("Unable to register the selection as a shortcut", "Error")
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
    message.message("Shortcut %s: [i]%s[/i]\nTarget: [i]%s[/i]" % (keyword, name.decode("utf-8"), shortcut), "Success")


@CommandHandler.register("Remove shortcut...", args=[""], subcmds=True)
def remove_shortcut(name=None):
    if name is None:  # Register subcommands
        shortcuts_dict = load_shortcuts()
        return [key.encode("utf-8") for key in shortcuts_dict]
    elif name == "":
        message.message("Press tab to select a shortcut to remove", "Error")
    else:
        if CommandHandler.remove(name):
            shortcuts_dict = load_shortcuts()  # Load shortcuts from the config file
            shortcuts_dict.pop(name.decode("utf-8"))  # Remove shortcut
            save_shortcuts(shortcuts_dict)  # Write back to the file
            message.message("Shortcut removed: [i]%s[/i]" % name.decode("utf-8"), "Success")
        else:
            message.message("Unable to remove shortcut: [i]%s[/i]" % name.decode("utf-8"), "Error")


def test():
    print "Success"


@Hook.register("CAPITAL", up_down="up")
def caps_up():
    cmd_win.call(cmd_win.run_command)


@Hook.register("CAPITAL", up_down="down")
def caps_down():
    cmd_win.call(cmd_win.show)


if __name__ == '__main__':
    t0 = time.time()
    app = QtGui.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    cmd_win = CommandWindow()
    CommandHandler.main_gui = cmd_win  # Make the main GUI available to other modules through the command handler
    CommandHandler.load_commands(ignore=cmd_win.ignore_modules)
    # print "Loaded commands:\n", CommandHandler.print_commands(), "\n"
    # print "Registered key combinations:\n", Hook.print_combos(), "\n"
    Hook.start()
    if "no-splash" not in sys.argv:
        msg = "Started in %d ms\nCommands: %d\nHotkeys: %d" % (1000 * (time.time() - t0), len(CommandHandler.command_list),
                                                               len(Hook.combos))
        message.message(msg, "automate 0.1.0", timeout=2000)
    app.exec_()

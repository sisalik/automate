import time
import re
import json

from PyQt4 import QtCore, QtGui

from input_hook import Hook
from command_handler import CommandHandler
import message


class CommandWindow(QtGui.QWidget):

    show_signal = QtCore.pyqtSignal()
    hide_signal = QtCore.pyqtSignal()
    fade_signal = QtCore.pyqtSignal()
    message_signal = QtCore.pyqtSignal(str, str, int)

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
        self.show_signal.connect(self.on_show)
        self.hide_signal.connect(self.on_hide)
        self.fade_signal.connect(self.on_fade)
        self.message_signal.connect(self.on_message)

        # Initialise some values
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

    def on_show(self):
        if time.time() - self.last_shown < 0.25:  # Double tap caps lock to enter Google search
            CommandHandler.get_subcmds("Google...")
            self.help_text.setText(CommandHandler.active_command)
        self.last_shown = time.time()

        self.setWindowOpacity(self.default_alpha)
        self.show()
        self.center()
        for i in xrange(5):  # Seems to be necessary for some reason
            self.activateWindow()
            time.sleep(0.02)

    def on_hide(self):
        self.on_fade_finished()

    def on_fade(self):
        self.fade()

    def on_suggestions(self, suggestions):
        pattern = self.get_text()
        if '\\' in pattern:  # Folder navigation mode
            pattern = pattern[pattern.rfind('\\') + 1:]
        self.tip_box.set_text(suggestions, pattern)

    def on_message(self, text, title, timeout):
        self.msg = message.Message(text, title, timeout)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Up:
            self.on_up()
        elif e.key() == QtCore.Qt.Key_Down:
            self.on_down()
        elif e.key() == QtCore.Qt.Key_Tab:
            self.on_tab()
        elif e.key() == QtCore.Qt.Key_Escape:
            self.on_esc()

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
        QtGui.QMessageBox.about(self, "About automate 0.1.0", "This is one of the best programs available.")


class TipBox(object):

    def __init__(self, parent, (x0, y0), (w, h), max_rows):
        self.parent = parent
        self.max_rows = max_rows
        self.w = w
        self.h = h

        self.rows = 0
        self.selected = 0

        # Get the highlight colour from the master stylesheet
        self.highlight_colour = re.search(r"QLabel#tip_line[\S\s]*?selection-color:\s*(.*?)\s*;",
                                          self.parent.styleSheet()).group(1)

        # Create label widgets
        self.lines = []
        for i in xrange(self.max_rows):
            line = QtGui.QLabel(parent=self.parent)

            x = x0
            y = y0 + i * self.h
            line.setGeometry(QtCore.QRect(x, y, self.w, self.h))
            line.setObjectName("tip_line")
            line.mousePressEvent = lambda e, i=i: self.on_click(e, i)
            self.lines.append(line)

    def highlight(self, text, pattern):
        text = text.decode("utf-8")
        pattern = pattern.decode("utf-8")
        start = 0
        for c in pattern.lower():
            pos = text.lower().find(c, start)
            if pos != -1:
                highlighted = r'<span style="color:%s;">%s</span>' % (self.highlight_colour, text[pos])
                start = pos + len(highlighted)
                text = text[:pos] + highlighted + text[pos + 1:]
        return "<html><head/><body><p>%s</p></body></html>" % text
        # return r"""
        #     <html>
        #         <head/>
        #         <body>
        #             <table valign="middle">
        #                 <tr>
        #                     <td width=25><img src="C:\Windows\winsxs\amd64_microsoft-windows-dxp-deviceexperience_31bf3856ad364e35_6.1.7600.16385_none_a31a1d6b13784548\settings.ico" height="20"/></td>
        #                     <td>%s</td>
        #                 </tr>
        #             </table>
        #         </body>
        #     </html>""" % text

    def set_text(self, content, pattern=None):
        content = list(content)  # In case it's a generator
        self.content = content

        for line, text in zip(self.lines, content):
            if pattern:
                line.setText(self.highlight(text, pattern))
            else:
                line.setText(text)

        self.selected = 0
        self.select(self.selected)
        self.rows = min(len(self.content), self.max_rows)

        self.parent.slide(self.h * self.rows)

    def get_selection(self):
        temp = QtGui.QTextDocument()
        temp.setHtml(self.lines[self.selected].text())
        text = temp.toPlainText()  # No icons
        # text = temp.toPlainText()[3:-1]
        return unicode(text).encode("utf-8")

    def select(self, index):
        for i, line in enumerate(self.lines):
            if i == index:
                line.setProperty("selected", True)
            else:
                line.setProperty("selected", False)
            line.setStyleSheet("")  # Update stylesheet

    def down(self,):
        if 0 <= self.selected < self.rows - 1:
            self.selected += 1
        else:
            self.selected = 0
        self.select(self.selected)

    def up(self):
        if 0 < self.selected < self.rows:
            self.selected -= 1
        else:
            self.selected = self.rows - 1
        self.select(self.selected)

    def on_click(self, event, index):
        self.selected = index
        caps_up()


@CommandHandler.register("Exit")
def exit():
    Hook.stop()
    app.quit()


@Hook.register("CAPITAL", up_down="up")
def caps_up():
    command = cmd_win.get_command()

    if command:
        subcommand_mode = CommandHandler.active_command is not None
        if CommandHandler.run(command) and not subcommand_mode:
            cmd_win.history.insert(0, command)
        cmd_win.fade_signal.emit()
    else:
        cmd_win.hide_signal.emit()


@Hook.register("CAPITAL", up_down="down")
def caps_down():
    cmd_win.show_signal.emit()


if __name__ == '__main__':
    t0 = time.time()
    app = QtGui.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    cmd_win = CommandWindow()
    CommandHandler.load_commands(ignore=cmd_win.ignore_modules)
    # print "Loaded commands:\n", CommandHandler.print_commands(), "\n"
    # print "Registered key combinations:\n", Hook.print_combos(), "\n"
    Hook.start()
    msg = "Started in %d ms\nCommands: %d\nHotkeys: %d" % (1000 * (time.time() - t0), len(CommandHandler.command_list),
                                                           len(Hook.combos))
    message.message(msg, "automate 0.1.0")
    app.exec_()

import struct
import ctypes
import thread
import os
import glob
import re

import win32com.client
from pywintypes import com_error
from PyQt4 import QtCore

import autocomplete
from message import message


class AutocompleteThread(QtCore.QThread):

    suggestions = QtCore.pyqtSignal(list)

    def __init__(self, ac_function, search_target):
        QtCore.QThread.__init__(self)
        self.ac_function = ac_function
        self.search_target = search_target

    def run(self):
        matches = self.ac_function(self.search_target)
        self.suggestions.emit(matches)


class CommandHandler(object):

    default_ac_delay = 0  # Default autocomplete delay (ms)

    ac_delay = default_ac_delay
    ac_timer = QtCore.QTimer()
    command_list = []
    active_command = None

    @classmethod
    def load_commands(cls, ignore):
        """Import all .py files in a folder. Based on a solution by Anurag Uniyal at http://stackoverflow.com/a/1057534"""
        modules = glob.glob(os.path.dirname(__file__)+"/commands/*.py")
        for f in modules:
            module_file = os.path.basename(f)[:-3]
            if module_file not in ignore:
                module = "commands." + module_file
                __import__(module, locals(), globals())

    @classmethod
    def register(cls, alias, callback=None, args=[], subcmds=False):
        """Decorator for registering commands."""
        # Called as a decorator?
        if callback is None:
            def register_decorator(f):
                cls.register(alias, callback=f, args=args, subcmds=subcmds)
                return f
            return register_decorator
        else:
            command = dict(alias=alias, callback=callback, args=args, subcmds=subcmds)
            cls.command_list.append(command)

    @classmethod
    def remove(cls, alias):
        for command in cls.command_list:
            if command['alias'] == alias:
                cls.command_list.remove(command)
                return True  # Success
        return False  # Couldn't find the command

    @classmethod
    def run(cls, text):
        python_architecture = struct.calcsize("P") * 8  # Python installation: 32- or 64-bit
        # If 32-bit Python is used, the System32 folder is normally redirected. This causes some applications to be impossible
        # to run. The following disables this redirection.
        if python_architecture == 32:
            old_value = ctypes.c_long()
            ctypes.windll.kernel32.Wow64DisableWow64FsRedirection(old_value)

        if cls.active_command:
            print "Command:", cls.active_command, ">", text
            for command in cls.command_list:
                if command['alias'] == cls.active_command:
                    thread.start_new_thread(command['callback'], (text,))
                    cls.reset_mode()
                    return True

        print "Command:", text
        for command in cls.command_list:
            if command['alias'] == text:
                thread.start_new_thread(command['callback'], tuple(command['args']))
                return True

        try:
            shell.Run('"' + text.decode("utf-8").encode("cp1252") + '"')
        except com_error:
            if re.search(r"\.\w+", text) is not None:  # Might be a URL. Append 'http://' and try again.
                try:
                    shell.Run('"http://' + text.decode("utf-8").encode("cp1252") + '"')
                except com_error:
                    message("Cannot execute: [i]%s[/i]" % text.decode("utf-8"), "Invalid command")
            else:
                message("Cannot execute: [i]%s[/i]" % text.decode("utf-8"), "Invalid command")
            return False
        else:
            return True

    @classmethod
    def reset_mode(cls):
        cls.active_command = None
        cls.autocomplete_function = cls.get_command_matches
        cls.ac_delay = cls.default_ac_delay

    @classmethod
    def get_subcmds(cls, cmd):
        cmd_list = None

        if cls.active_command and "..." in cmd:
            for command in cls.command_list:
                if command['alias'] == cls.active_command:
                    cmd_list = command['callback'](cmd)
                    break
        else:
            for command in cls.command_list:
                if command['alias'] == cmd and command['subcmds']:
                    cmd_list = command['callback']()
                    cls.active_command = command['alias']
                    break

        if type(cmd_list) is list:
            cls.autocomplete_function = cls.list_matcher(cmd_list)
        elif cmd_list:  # hopefully a callable type
            cls.autocomplete_function = cmd_list
        else:
            return False
        return True

    @classmethod
    def on_ac_timeout(cls):
        """Autocomplete timeout"""
        cls.ac_timer.stop()
        cls.ac_thread.start()

    @classmethod
    def get_matches(cls, text):
        cls.ac_thread = AutocompleteThread(cls.autocomplete_function, text)
        cls.ac_timer.timeout.connect(cls.on_ac_timeout)
        cls.ac_timer.stop()
        cls.ac_timer.start(cls.ac_delay)
        return cls.ac_thread

    @classmethod
    def get_command_matches(cls, text):
        # Only trigger matching when text is not empty
        if text:
            matcher = autocomplete.Matcher()

            if '\\' in text:
                path = text[:text.rfind('\\')]
                if os.path.isfile(path):
                    return []
                try:
                    strings = [s.decode("cp1252").encode("utf-8") for s in os.listdir(path + '\\')]
                except WindowsError:
                    return []
                else:
                    matcher.set_pattern(text[text.rfind('\\') + 1:])
            else:
                matcher.set_pattern(text)
                strings = []
                for item in cls.command_list:
                    alias = item['alias']
                    if alias:
                        strings.append(alias)

            matches = matcher.score(strings)
            matches.sort(key=lambda k: k['score'], reverse=True)
            return [match['text'] for match in matches]
        else:
            return []

    @classmethod
    def list_matcher(cls, list):
        @classmethod
        def inner_list_matcher(cls, text):
            matcher = autocomplete.Matcher()
            matcher.set_pattern(text)
            matches = matcher.score(list)
            matches.sort(key=lambda k: k['score'], reverse=True)
            return [match['text'] for match in matches]
        return inner_list_matcher

    @classmethod
    def print_commands(cls):
        return "\n".join([cmd['alias'] for cmd in cls.command_list]) + "\nTOTAL: " + str(len(cls.command_list))

shell = win32com.client.Dispatch("WScript.Shell")
CommandHandler.autocomplete_function = CommandHandler.get_command_matches

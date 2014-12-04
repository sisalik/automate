"""Defines a class that limits an application to a single instance.
Based on a post by Dragan Jovelic at http://code.activestate.com/recipes/474070/"""

from win32event import CreateMutex
from win32api import CloseHandle, GetLastError
from winerror import ERROR_ALREADY_EXISTS


class SingleInstance:
    def __init__(self):
        self.mutex_name = "testmutex_{D0E858DF-985E-4907-B7FB-8D732C3FC3B9}"
        self.mutex = CreateMutex(None, False, self.mutex_name)
        self.last_error = GetLastError()

    def alerady_running(self):
        return (self.last_error == ERROR_ALREADY_EXISTS)

    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)

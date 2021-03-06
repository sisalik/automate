from ctypes import cdll
import subprocess

import win32gui
import win32con

from command_handler import CommandHandler


def get_all_windows():
    def enum_handler(hwnd, titles):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).decode("cp1252").encode("utf-8")
            if title:
                titles.append({'title': title, 'hwnd': hwnd})

    titles = []
    win32gui.EnumWindows(enum_handler, titles)
    return titles


def get_processes():
    cmd = 'wmic process get Caption'  # ,Commandline,Processid
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    processes = [line.rstrip() for line in proc.stdout]
    return processes[1:-1]


def find_win(title):
    for win in get_all_windows():
            if win['title'] == title:
                return win['hwnd']
    return None


@CommandHandler.register("Switch to...", subcmds=True, label='System', priority=0)
def switch_to(title=None):
    if title is None:  # Register command
        win_titles = [win['title'] for win in get_all_windows()]
        return win_titles
    else:
        hwnd = find_win(title)
        win32gui.SetForegroundWindow(hwnd)
        win_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if win_style & win32con.WS_MINIMIZE:  # The window is minimized
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        else:  # The window is inactive
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)


@CommandHandler.register("Close...", subcmds=True, label='System', priority=0)
def close(title=None):
    if title is None:  # Register command
        win_titles = [win['title'] for win in get_all_windows()]
        return win_titles
    else:
        hwnd = find_win(title)
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)


@CommandHandler.register("Kill...", subcmds=True, label='System', priority=0)
def kill(process=None):
    if process is None:  # Register command
        return get_processes()
    else:
        subprocess.Popen('taskkill /f /im ' + process, shell=True)


@CommandHandler.register("Screen off", label='System', priority=0)
def screen_off():
    for win in get_all_windows():
        if win['title'] == "Program Manager":
            win32gui.SendMessage(win['hwnd'], win32con.WM_SYSCOMMAND, win32con.SC_MONITORPOWER, 2)


@CommandHandler.register("Sleep", label='System', priority=0)
def sleep():
    # SetSuspendState only returns after the computer resumes, therefore causing errors. Enclosed in a try-except block.
    try:
        cdll.LoadLibrary("powrprof.dll").SetSuspendState(0, 0, 0)
    except ValueError:
        pass


@CommandHandler.register("Hibernate", label='System', priority=0)
def hibernate():
    try:
        cdll.LoadLibrary("powrprof.dll").SetSuspendState(1, 0, 0)
    except ValueError:
        pass

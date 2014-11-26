"""
Keyboard hook part adapted from http://stackoverflow.com/a/16430918
"""

from ctypes import windll, wintypes, CFUNCTYPE, POINTER, c_int, c_short, c_uint8, c_void_p, byref
from collections import namedtuple
import threading

import win32con
import win32api
import win32event
import win32gui
from PyQt4 import QtCore, QtGui

from keycodes import keycodes

KeyboardEvent = namedtuple("KeyboardEvent", "event_type, key_code, scan_code, alt_pressed, time")
MouseEvent = namedtuple("MouseEvent", "event_type, message, x, y, delta")

kb_event_types = {win32con.WM_KEYDOWN: 'down',
                  win32con.WM_KEYUP: 'up',
                  win32con.WM_SYSKEYDOWN: 'down',  # Used for Alt key.
                  win32con.WM_SYSKEYUP: 'up',  # Used for Alt key.
                  }
mouse_event_types = {win32con.WM_LBUTTONDOWN: "left button down",
                     win32con.WM_LBUTTONUP: "left button up",
                     win32con.WM_MBUTTONDOWN: "middle button down",
                     win32con.WM_MBUTTONUP: "middle button up",
                     win32con.WM_RBUTTONDOWN: "right button down",
                     win32con.WM_RBUTTONUP: "right button up",
                     win32con.WM_MOUSEMOVE: "move",
                     win32con.WM_MOUSEWHEEL: "wheel",
                     0x20B: "xbutton down",  # WM_XBUTTONDOWN - not included in win32con
                     0x20C: "xbutton up",  # WM_XBUTTONUP
                     0x20E: "horizontal wheel"}  # WM_MOUSEHWHEEL (horizontal wheel)


class HookThread(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        # Our low level handler signature.
        CMPFUNC = CFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))
        # Convert the Python handlers into C pointer.
        pointer_kb = CMPFUNC(Hook.ll_kb_handler)
        pointer_mouse = CMPFUNC(Hook.ll_mouse_handler)

        # Hook both key up and key down events for common keys (non-system).
        kb_hook_id = windll.user32.SetWindowsHookExA(win32con.WH_KEYBOARD_LL,
                                                     pointer_kb, win32api.GetModuleHandle(None), 0)
        mouse_hook_id = windll.user32.SetWindowsHookExA(win32con.WH_MOUSE_LL,
                                                        pointer_mouse, win32api.GetModuleHandle(None), 0)
        Hook.hook_thread_id = win32api.GetCurrentThreadId()

        # Pump messages
        msg = wintypes.MSG()
        while windll.user32.GetMessageA(byref(msg), None, 0, 0) != 0:
            if msg.message == win32con.WM_QUIT:
                break
            try:
                win32gui.TranslateMessage(byref(msg))
                win32gui.DispatchMessage(byref(msg))
            except SystemError:
                pass

        windll.user32.UnhookWindowsHookEx(kb_hook_id)
        windll.user32.UnhookWindowsHookEx(mouse_hook_id)


class Hook(object):

    combos = []  # Registered key combinations
    keys_down = set()  # Keys currently held down
    stop_event = win32event.CreateEvent(None, 0, 0, None)

    @classmethod
    def start(cls):
        # cls.hook_thread = threading.Thread(target=cls.listen_loop)
        cls.hook_thread = HookThread()
        cls.hook_thread.start()

    @classmethod
    def stop(cls):
        win32api.PostThreadMessage(cls.hook_thread_id, win32con.WM_QUIT, 0, 0)

    @classmethod
    def register(cls, combo_str, callback=None, args=None, up_down='down'):
        """
        Decorator for registering hotkeys.
        Inspired by http://project-2501.net/index.php/2014/06/global-hot-keys-in-python-for-windows/
        """
        # Called as a decorator?
        if callback is None:
            def register_decorator(f):
                cls.register(combo_str, f, args, up_down)
                return f
            return register_decorator
        else:
            combo = {}
            try:
                combo['keys'] = set(keycodes[key_str] for key_str in combo_str.replace(' ', '').split('+'))
            except KeyError as e:
                print "Invalid key code %s specified in hotkey for function '%s'" % (e, callback.__name__)
            else:
                combo['up_down'] = up_down
                combo['callback'] = callback
                combo['args'] = args
                cls.combos.append(combo)

    @classmethod
    def kb_handler(cls, event):
        # key_state = (c_uint8 * 256)()
        # windll.user32.GetKeyboardState(byref(key_state))
        # print [i for i in key_state]

        repeat_key = False
        remove = False
        block = False

        if event.event_type == 'down' and event.key_code not in cls.keys_down:
            cls.keys_down.add(event.key_code)
        elif event.event_type == 'up' and event.key_code in cls.keys_down:
            remove = True
        else:
            repeat_key = True

        # print "Held:", '+'.join([keycodes[key] for key in cls.keys_down])

        for combo in cls.combos:
            if cls.keys_down == combo['keys']:
                if event.event_type == combo['up_down'] and not repeat_key:  # Remove last part to allow repeat triggering
                    # If the callback function has an argument called 'event',
                    # pass the event structure to the callback function when called
                    if 'event' in combo['callback'].func_code.co_varnames:
                        ret = combo['callback'](event)
                    elif combo['args']:
                        ret = combo['callback'](*combo['args'])
                    else:
                        ret = combo['callback']()
                    # In case the function returns an integer or boolean, assume it's the blocking flag
                    if type(ret) in (bool, int):
                        block = ret
                    else:
                        block = True
                elif repeat_key:
                    block = True
        # if block:
        #     print "Blocked", '+'.join([keycodes[key] for key in cls.keys_down])
        # else:
        #     print "NOT blocked", '+'.join([keycodes[key] for key in cls.keys_down])
        if remove:
            cls.keys_down.remove(event.key_code)
        return block  # Pass keystroke

    @classmethod
    def mouse_handler(cls, event):
        block = False
        for combo in cls.combos:
            if set([event.message]) | cls.keys_down == combo['keys']:
                block = True
                # If the callback function has an argument called 'event',
                # pass the event structure to the callback function when called
                if 'event' in combo['callback'].func_code.co_varnames:
                    ret = combo['callback'](event)
                elif combo['args']:
                    ret = combo['callback'](*combo['args'])
                else:
                    ret = combo['callback']()
                # In case the function returns something, assume it's the blocking flag
                if ret is not None:
                    block = ret
                else:
                    block = True
        return block

    @classmethod
    def ll_kb_handler(cls, nCode, wParam, lParam):
        """
        Processes low level Windows keyboard events.
        """
        event = KeyboardEvent(kb_event_types[wParam], lParam[0], lParam[1], lParam[2] == 32, lParam[3])
        if not cls.kb_handler(event):  # Block not requested
            return windll.user32.CallNextHookEx(None, nCode, wParam, lParam)  # Call next hook
        else:
            return True  # Block event

    @classmethod
    def ll_mouse_handler(cls, nCode, wParam, lParam):
        """
        Processes low level Windows mouse events.
        """
        # Ignore WM_MOUSEMOVE events
        if wParam == win32con.WM_MOUSEMOVE:
            return windll.user32.CallNextHookEx(None, nCode, wParam, lParam)  # Call next hook

        # Calculate mouse wheel delta value (120 or -120)
        if lParam[2]:
            delta = c_short(lParam[2] >> 16).value
        else:
            delta = None

        # Fix coordinates at the edge of the screen not being integers
        if type(lParam[0]) is not int:
            x = 0
        else:
            x = lParam[0]
        if type(lParam[1]) is not int:
            y = 0
        else:
            y = lParam[1]

        # Construct event namedtuple
        event = MouseEvent(mouse_event_types[wParam], wParam, x, y, delta)

        if not cls.mouse_handler(event):  # Block not requested
            return windll.user32.CallNextHookEx(None, nCode, wParam, lParam)  # Call next hook
        else:
            return True  # Block event

    @classmethod
    def print_combos(cls):
        out = []
        for combo in cls.combos:
            out.append("%s\t%s %s" % (combo['callback'].__name__ + '\t', '+'.join([keycodes[key] for key in combo['keys']]),
                                      combo['up_down']))
        return '\n'.join(out) + "\nTOTAL: " + str(len(cls.combos))


def send_combo(combo_str, repeat=1):
    key_strings = combo_str.replace(' ', '').split('+')

    for i in xrange(repeat):
        for key_str in key_strings:
            win32api.keybd_event(keycodes[key_str], 0, 0, 0)
        for key_str in key_strings[::-1]:  # Reversed list
            win32api.keybd_event(keycodes[key_str], 0, win32con.KEYEVENTF_KEYUP, 0)


if __name__ == '__main__':
    @Hook.register("L", up_down="up")
    def l_up(event):
        print "UP!"

    @Hook.register("L", up_down="down")
    def l_down():
        print "DOWN!"

    @Hook.register("LCONTROL + T")
    def print_threads():
        print threading.enumerate()

    @Hook.register("MOUSEWHEEL")
    @Hook.register("MOUSEHWHEEL")
    def mouse(event):
        print "You scrolled",
        if event.delta > 0:
            print "up",
        else:
            print "down",
        print "at", event.x, event.y

    def print_text(text):
        print text

    Hook.register("LCONTROL + Q", callback=Hook.stop)
    Hook.register("LCONTROL + P", callback=print_text, args="Print this shit")

    from subprocess import call
    Hook.register("LCONTROL + M", callback=call, args="control main.cpl")

    Hook.start()
    app = QtGui.QApplication([])  # Needed
    app.exec_()

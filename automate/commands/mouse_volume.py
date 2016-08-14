import win32api

from input_hook import Hook, send_combo
# from message import message


def adjust_volume(direction, amount=1):
    if direction == "up":
        key = "VOLUME_UP"
    elif direction == "down":
        key = "VOLUME_DOWN"
    send_combo(key, amount)


@Hook.register("MOUSEWHEEL")
def mouse_wheel(event):
    # GetSystemMetrics documentation: https://msdn.microsoft.com/en-gb/library/windows/desktop/ms724385(v=vs.85).aspx
    screen_w = win32api.GetSystemMetrics(0)  # The width of the primary monitor
    desktop_w = win32api.GetSystemMetrics(78)  # The width of the virtual desktop (all monitors)
    desktop_left = win32api.GetSystemMetrics(76)  # The x-coordinate of the left side of the virtual screen
    # message("x: %d" % event.x, "Debug")
    if event.x == 0 or event.x == desktop_left or event.x == screen_w:
        amount = 3
    elif event.x == screen_w - 1 or event.x == desktop_w - 1 or event.x == -1:
        amount = 1
    elif event.y == 0:
        send_combo("LWIN + W")
        send_combo("LWIN + Q")
        return 1
    else:
        return 0  # Do not block mouse scrolling elsewhere

    if event.delta < 0:
        direction = "down"
    else:
        direction = "up"

    adjust_volume(direction, amount)
    return 1

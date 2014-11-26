import win32api

from input_hook import Hook, send_combo


def adjust_volume(direction, amount=1):
    if direction == "up":
        key = "VOLUME_UP"
    elif direction == "down":
        key = "VOLUME_DOWN"
    send_combo(key, amount)


@Hook.register("MOUSEWHEEL")
def mouse_wheel(event):
    screen_w = win32api.GetSystemMetrics(0)
    if event.x == 0:
        amount = 3
    elif event.x == screen_w - 1:
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

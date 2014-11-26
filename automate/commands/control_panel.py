"""
Adds commands for all Control Panel items (including third-party additions).
"""
import _winreg as reg
import subprocess


def get_values(key):
    keys = {}
    key_count = reg.QueryInfoKey(key)[0]
    for i in xrange(key_count):
        try:
            key_name = reg.EnumKey(key, i)
            sub_key = reg.OpenKey(key, key_name)
            val = reg.QueryValue(sub_key, None)
            if val:
                keys[key_name] = val.decode("cp1252").encode("utf-8")
        except WindowsError as e:
            if e.errno == 22:  # No more data is available
                break
    return keys

registry = reg.ConnectRegistry(None, reg.HKEY_LOCAL_MACHINE)
cpanel_items = reg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Explorer\ControlPanel\NameSpace", 0,
                           reg.KEY_WOW64_64KEY + reg.KEY_READ)

if __name__ != "__main__":
    from command_handler import CommandHandler
    for k, v in get_values(cpanel_items).items():
        CommandHandler.register(v, subprocess.Popen, ["explorer shell:::" + k])
else:
    print get_values(cpanel_items)

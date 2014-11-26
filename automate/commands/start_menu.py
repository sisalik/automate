"""
Adds commands for all Start Menu executables, excluding some obvious unwanted items, such as uninstallers.
"""

import os
import subprocess
from itertools import chain

# import win32com.client


def get_shortcuts(indir):
    """
    Find all shortcuts (.lnk) in the given folder (indir) and retrieve their target locations.
    """

    # shell = win32com.client.Dispatch("WScript.Shell")
    for root, dirs, filenames in os.walk(indir):
        for f in filenames:
            if f[-4:] == ".lnk" and "uninstall" not in f[:-4].lower():
                yield {'name': f[:-4].decode("cp1252").encode("utf-8"), 'target': root + '\\' + f}
                # shortcut = shell.CreateShortcut(root + '\\' + f)
                # if ".exe" in shortcut.TargetPath.lower() and "install" not in f.lower():
                    # shortcuts.append({'name': f[:-4].decode("latin-1").encode("utf-8"),
                                      # 'target': os.path.expandvars(' '.join([shortcut.TargetPath, shortcut.Arguments]))})
                # elif not shortcut.TargetPath:
                    # print "No target for", f

all_users = os.environ["SYSTEMDRIVE"] + r"\ProgramData\Microsoft\Windows\Start Menu"
current_user = os.environ["APPDATA"] + r"\Microsoft\Windows\Start Menu"

if __name__ != "__main__":
    from command_handler import CommandHandler
    for s in chain(get_shortcuts(all_users), get_shortcuts(current_user)):
        CommandHandler.register(s['name'], subprocess.Popen, ["explorer " + s['target']])
else:
    for s in chain(get_shortcuts(all_users), get_shortcuts(current_user)):
        print s

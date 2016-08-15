"""
An example module with some functions and hotkeys defined.
"""

import time

from command_handler import CommandHandler
from input_hook import Hook
from message import message


@CommandHandler.register("Test command", label='Test')
def fun():
    message("Hello world! :)\n<span style=\"color:red\">This text is red.", "Message")


@CommandHandler.register("Subcommand test", label='Test', subcmds=True)
def fun2(arg=None):
    # If the argument is None, return a list of available subcommands
    if arg is None:
        return ["Sub 1", "Sub 2", "Sub 3", "More..."]

    # Otherwise, the argument contains the name of the subcommand
    elif arg == "Sub 1":
        message("Sub 1")
    elif arg == "Sub 2":
        message("Sub 2 loading...")
        time.sleep(5)
        message("Done!")
    elif arg == "Sub 3":
        message("Sub 3", "Important message")
    elif arg == "More...":
        return ["Sub 4", "Sub 5"]

    elif arg == "Sub 4":
        message("Sub 4")
    elif arg == "Sub 5":
        message("Sub 5")


@Hook.register("LCONTROL + L")
def fun3():
    message("Looks like you pressed Ctrl + L, buddy.", "Notification")

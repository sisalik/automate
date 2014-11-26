"""
A test module full of very useful functions.
"""

import time

from command_handler import CommandHandler
from message import message


@CommandHandler.register("Commanda")
def fun():
    message("Message", "Fun fun 1")


@CommandHandler.register("Subcommander", subcmds=True)
def fun2(arg=None):
    if arg is None:  # Register subcommands
        return ["Sub1", "Sub2", "Sub3", "More..."]

    elif arg == "Sub1":
        print "supersub1...",
        time.sleep(5)
        print "done!"
    elif arg == "Sub2":
        print "supersub2"
    elif arg == "Sub3":
        print "supersub3"
    elif arg == "More...":
        print "This one takes a while to return"
        time.sleep(3)
        return ["Sub4", "Sub5", "Sub6"]

    elif arg == "Sub4":
        print "supersub4"
    elif arg == "Sub5":
        print "supersub5"
    elif arg == "Sub6":
        print "supersub6"

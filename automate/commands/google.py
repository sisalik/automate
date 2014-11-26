# import time

from PyQt4 import QtCore

from command_handler import CommandHandler
from message import message
import g_suggest

g_suggest.tld = "co.uk"
timer = QtCore.QTimer()


@classmethod
def google_suggest(cls, query):
    CommandHandler.ac_delay = 500
    if len(query) > 2:
        return [query] + [r.encode("utf-8") for r in g_suggest.single_suggest(query)]
        # print "This takes a while"
        # time.sleep(3)
        # import autocomplete
        # matcher = autocomplete.Matcher()
        # matcher.set_pattern(query)
        # matches = matcher.score(["Alpha", "Beta", "Gamma", "Delta", "Epsilon"])
        # matches.sort(key=lambda k: k['score'], reverse=True)
        # return [match['text'] for match in matches]
    else:
        return []


@CommandHandler.register("Google...", subcmds=True)
def google(query=None):
    if query is None:  # Register subcommands
        return google_suggest
    elif query != "Google...":  # Terrible attempt at fix
        CommandHandler.reset_mode()
        CommandHandler.run("https://www.google.co.uk/search?q=" + query)

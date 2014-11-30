from command_handler import CommandHandler
import g_suggest

g_suggest.tld = "co.uk"


@classmethod
def google_suggest(cls, query):
    CommandHandler.ac_delay = 500
    if len(query) > 2:
        return [query] + [r.encode("utf-8") for r in g_suggest.single_suggest(query)]
    else:
        return []


@CommandHandler.register("Google...", subcmds=True)
def google(query=None):
    if query is None:  # Register subcommands
        return google_suggest
    elif query != "Google...":  # Terrible attempt at a fix
        CommandHandler.reset_mode()
        CommandHandler.run("https://www.google.co.uk/search?q=" + query)

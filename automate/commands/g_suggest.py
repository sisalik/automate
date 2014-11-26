"""
Simplified from https://gist.github.com/eristoddle/3750993
"""

from urllib import quote
import urllib2
try:
    import json
except ImportError:
    import simplejson as json

# Set the user agent to a common browser user agent string to get always utf-8 encoded response
headers = {'User-agent': 'Mozilla/5.0'}
tld = "com"


def get_suggestion(query):
    """Query Google suggest service"""
    suggestions = []
    if query:
        if isinstance(query, unicode):
            query = query.encode('utf-8')
        query = quote(query)
        # url = "http://clients1.google.%s/complete/search?q=%s&json=t&ds=&client=serp" % (tld, query)
        req = urllib2.urlopen("http://clients1.google.%s/complete/search?q=%s&json=t&ds=&client=serp" % (tld, query))
        encoding = req.headers['content-type'].split('charset=')[-1]
        content = unicode(req.read(), encoding)
        result = json.loads(content)
        suggestions = [i for i in result[1]]
    return suggestions


def single_suggest(query):
    """Provide suggestions via AJAX"""
    result = get_suggestion(query)
    return result[1:]


if __name__ == "__main__":
    # print single_letter_recursive_suggest("patio door handle")
    try:
        print single_suggest("kerli k")
    except IOError:
        print "Unable to connect to Google"

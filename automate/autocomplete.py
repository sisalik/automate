"""
Autocomplete functionality. Adapted from http://crossplatform.net/sublime-text-ctrl-p-fuzzy-matching-in-python/
"""

import re


class Matcher():

    def __init__(self):
        self.pattern = ''

    def set_pattern(self, pattern):
        self.pattern = pattern
        self.re_pattern = re.compile('.*?'.join(map(re.escape, list(pattern))), re.IGNORECASE)

    def score_item(self, string):
        match = self.re_pattern.search(string)
        if match is None:
            return 0
        else:
            return 100.0 / ((1 + match.start()) * (match.end() - match.start() + 1))

    def score(self, search_list):
        matches = []
        for s in search_list:
            score = self.score_item(s)
            if score:
                matches.append({'text': s, 'score': score})

        return matches


if __name__ == '__main__':
    fuzzy_matcher = Matcher()
    fuzzy_matcher.set_pattern('this o')  # Set a pattern to match aganinst
    print fuzzy_matcher.score_item('This is string one')  # Score for this string against the pattern
    print fuzzy_matcher.score_item('This is string two')  # And so on...

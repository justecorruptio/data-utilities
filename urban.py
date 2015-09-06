#!/usr/bin/env python

import json
import urllib2
import sys

WIDTH = 80
URBAN_URL = 'http://api.urbandictionary.com/v0/define?term=%s'

if len(sys.argv) < 2:
    sys.stderr.write("usage: urban <term>\n")
    sys.exit(1)

term = '+'.join(sys.argv[1:])

try:
    resp = urllib2.urlopen(URBAN_URL % (term,))
    data = json.loads(resp.read())
except Exception:
    sys.stderr("error contacting urban dictionary.\n")
    sys.exit(1)

if data['result_type'] != 'exact':
    sys.stderr("no definitions.\n")
    sys.exit(1)

definitions = data['list']
definitions.sort(key=lambda x: -1.0 * x['thumbs_up']/x['thumbs_down'])
definitions = definitions[:3]

def render_def(n, d):
    res = ''
    line = "%d)" % (n + 1,)
    for word in d.split():
        if len(line) + 1 + len(word) > WIDTH:
            res += line + '\n'
            line = "  "
        line += ' ' + word
    res += line + '\n'
    return res

sections = []
for n, entry in enumerate(definitions):
    section = render_def(n, entry['definition'])
    sections.append(section)

sys.stdout.write('\n'.join(sections))

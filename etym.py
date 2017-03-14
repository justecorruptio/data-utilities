#!/usr/bin/env python

import HTMLParser
import urllib2
import re
import sys

WIDTH = 80

if len(sys.argv) < 2:
    sys.stderr.write("usage: etym <term>\n")
    sys.exit(1)

URL = 'http://www.etymonline.com/index.php?term=%s'

term = '+'.join(sys.argv[1:])

try:
    resp = urllib2.urlopen(URL % (term,))
except Exception:
    sys.stderr.write('Network Error')
    sys.exit(1)

match = re.search(r'<div id="dictionary">(.*)<!-- DICTIONARY -->',
    resp.read(), re.M | re.S | re.I)
if not match:
    sys.stderr.write('Bad Data')
    sys.exit(1)

txt = match.group(0)
txt = re.sub('\n', '', txt)
txt = re.sub(r'<!--.*?-->', '', txt)
txt = re.sub(r'</?(div|dl|p)[^>]*>', '', txt)
txt = re.sub(r'<img.*?/(img)?>', '', txt)
txt = re.sub(r'<a [^>]+>', '\033[31m', txt)
txt = re.sub(r'</a>', '\033[39m', txt)

txt = re.sub(r'<dt[^>]*>(.*?)</dt>', r'\1\n', txt)
txt = re.sub(r'<dd[^>]*>(.*?)</dd>', r'\1\n\n', txt)
txt = re.sub(r'<span class="foreign">(.*?)</span>', '\033[3m\\1\033[23m', txt)
txt = re.sub(r'<blockquote>(.*?)</blockquote>',
    '\n\n    \033[38;5;241m\\1\033[39m\n\n', txt)

txt = re.sub(r'<(br|BR)>', '\n', txt, re.I)

txt = re.sub(r'\x0d', '', txt)

txt = HTMLParser.HTMLParser().unescape(txt)
txt = txt.strip()

def _len(s):
    return len(re.sub('\033\\[.*?m', '', s))

output = ''
for row in txt.split('\n'):
    indent = re.match('^( *)', row).group(1)
    line = indent
    for word in row.split():
        if _len(line) + 1 + _len(word) > WIDTH:
            output += line + '\n'
            line = indent
        line += ' ' + word
    output += line + '\n'

print output.encode('utf-8')

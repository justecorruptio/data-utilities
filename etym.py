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
txt = re.sub(r'<b>(.*?)</b>', '\033[1m\\1\033[22m', txt)

def blockquote(match):
    txt = match.group(1)
    txt = re.sub(r'<br>', '\n    ', txt, flags=re.I)
    txt = re.sub(r'<hr>', '--\n    ', txt, flags=re.I)
    txt = '\n\n    \033[38;5;244m%s\033[39m\n\n' % (txt,)
    return txt

txt = re.sub(r'<blockquote>(.*?)</blockquote>', blockquote, txt)

txt = re.sub(r'\x0d', '', txt)
txt = re.sub(r'\n{3,}', '\n\n', txt)

txt = HTMLParser.HTMLParser().unescape(txt)

txt = re.sub(r'<br>', '\n', txt, flags=re.I)
txt = re.sub(r'<hr>', '--\n', txt, flags=re.I)
txt = re.sub(r' *\n|\n *', '\n', txt)

def _len(s):
    return len(re.sub('\033\\[.*?m', '', s))

output = ''
for row in txt.split('\n'):
    indent = re.match('^( *)', row).group(1)
    line = []
    for word in row.split():
        if len(indent) + sum(map(_len, line)) + len(line) + _len(word) > WIDTH:
            output += indent + ' '.join(line) + '\n'
            line = []
        line.append(word)
    output += indent + ' '.join(line) + '\n'

output = output.strip()
print output.encode('utf-8')

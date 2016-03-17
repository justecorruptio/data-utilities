__garcon () {
    __GARCON_UNDO+=("$READLINE_LINE" "$READLINE_POINT")
    READLINE_LINE=$(
        python -c '
from base64 import b64encode, b64decode
import cPickle as pickle
import datetime, os, re, sys, time
from math import *

b64 = b64encode

def _from_unix_time(ts):
    return datetime.datetime.fromtimestamp(
        int(ts),
    ).strftime("%Y-%m-%d %H:%M:%S")

cmd = os.environ.get("READLINE_LINE")
if not cmd:
    sys.exit(1)

parts = re.findall(r"\"[^\"]*\"|\s+|\S+", cmd)

clean_parts = []
for part in parts:
    if re.match(r"^([.0-9]+|pi|e|\".*\")[)]*$", part):
        part = "(" + part + ")"
    if part == "time":
        part = "time.time()"
    if part == "ts":
        part = "_from_unix_time"
    clean_parts.append(part)

for i in xrange(0, len(parts), 2):
    head = "".join(parts[:i])
    tail = "".join(clean_parts[i:])
    try:
        compile(tail, "<dummy>", "eval")
    except:
        continue
    try:
        val = eval(tail)
        if val is None:
            continue
    except:
        continue
    if isinstance(val, float) and round(val, 8) == 0.:
        val = 0
    print head + str(val)
    break
else:
    print cmd
    sys.exit(1)
')
    READLINE_POINT=${#READLINE_LINE}
    return $?
}

__garcon_undo () {
    if [ ${#__GARCON_UNDO[@]} -eq 0 ] ; then
        return
    fi
    READLINE_LINE=${__GARCON_UNDO[-2]}
    READLINE_POINT=${__GARCON_UNDO[-1]}
    unset __GARCON_UNDO[${#__GARCON_UNDO[@]}-1]
    unset __GARCON_UNDO[${#__GARCON_UNDO[@]}-2]
}

bind -x '"ç":"__garcon"'
bind -x '"Ç":"__garcon_undo"'
bind -x '"÷":"__garcon"'
bind -x '"¿":"__garcon_undo"'
bind '"Æ":"\C-a\"\C-e\""'
bind '"æ":"\eb\"\ef\""'

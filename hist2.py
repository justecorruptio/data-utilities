import os, sys, tty, termios, re
from PIL import Image, ImageDraw
import cStringIO as StringIO
import base64

def get_cell_size():
    termios.tcflush(0, termios.TCIOFLUSH)
    term_attr = termios.tcgetattr(0)
    tty.setcbreak(0)

    sys.stdout.write("\x1b]1337;ReportCellSize\a")
    sys.stdout.flush()

    b = ''
    while True:
        b += sys.stdin.read(1)
        match = re.search(r'(\d+\.\d);(\d+\.\d)', b)
        if match:
            c_h, c_w = match.groups()
            break

    termios.tcsetattr(0, termios.TCSANOW, term_attr)

    return float(c_w), float(c_h)

def get_window_size():
    c_w, c_h = get_cell_size()
    h, w = os.popen('stty size').read().split()
    return int(int(w) * c_w), int(int(h) * c_h)


class Plot(object):
    def __init__(self, N, Z=3, rows=1):
        w, h = map(int, get_cell_size())
        h *= rows
        self.size = (w, h)
        self.Z = Z
        self.img = Image.new('RGBA', (Z * N, h))

    def line_plot(self, data, color=(0, 255, 255, 255)):
        w, h = self.size
        N = len(data)
        M = max(data)
        Z = self.Z

        line = [
            (Z * i, h - int(float(v) / M * h) - 1)
            for i, v in enumerate(data)
        ]
        draw = ImageDraw.Draw(self.img)
        draw.line(line, fill=color)

    def bar_plot(self, data, color=None):
        w, h = self.size
        N = len(data)
        M = max(data)
        Z = self.Z

        draw = ImageDraw.Draw(self.img)
        for i, v in enumerate(data):
            v = float(v) / M
            p = int(v * h)

            if color is None:
                c = int(v * 255)
                k = (c, 255 - c, 0, 255)
            else:
                k = color

            draw.rectangle([
                (Z * i + 1, h - 1),
                (Z * i + Z - 1, h - p - 1),
            ], fill=k)

    def output(self):
        buff = StringIO.StringIO()
        self.img.save(buff, format='PNG')

        sys.stdout.write("\x1b]1337;File=inline=1:%s\a" % (
            base64.b64encode(buff.getvalue()),
        ))
        sys.stdout.flush()

import random
N=100
#dat = [i for i in xrange(N)]
dat = [random.random() for i in xrange(N)]

plt = Plot(N, Z=3, rows=1)
#plt.line_plot(dat)
plt.bar_plot(dat)
plt.output()

print ''

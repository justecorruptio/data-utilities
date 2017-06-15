#!/usr/bin/env python -S

import os, sys, tty, termios, re
import base64
import random
from struct import pack


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


class PAM(object):
    def __init__(self, size):
        self.w, self.h = size

        self.data = [(0, 0, 0, 0)] * (self.w * self.h)

    def rect(self, pos, fill=(255, 0, 0, 0)):
        (a, b), (c, d) = pos
        if c < a:
            a, c = c, a
        if d < b:
            b, d = d, b

        for i in xrange(a, c + 1):
            for j in xrange(b, d + 1):
                self.data[j * self.w + i] = fill

    def as_string(self):
        s = """P7
WIDTH %d
HEIGHT %d
DEPTH 4
MAXVAL 255
TUPLTYPE RGB_ALPHA
ENDHDR\n""" % (self.w, self.h)

        for rgba in self.data:
            s += pack("BBBB", *rgba)

        return s


class Plot(object):
    def __init__(self, N, Z=3, rows=1):
        w, h = map(int, get_cell_size())
        h *= rows
        self.size = (w, h)
        self.Z = Z
        self.pam = PAM((Z*N, h))

    def line_plot(self, data, color=(0, 255, 255, 255)):
        w, h = self.size
        N = len(data)
        m = min(data)
        M = max(data) - m
        Z = self.Z

        line = [
            (Z * i, h - int(float(v - m) / M * h) - 1)
            for i, v in enumerate(data)
        ]
        draw = ImageDraw.Draw(self.img)
        draw.line(line, fill=color)

    def bar_plot(self, data, color=None):
        w, h = self.size
        N = len(data)
        m = min(data)
        M = max(data) - m
        Z = self.Z

        for i, v in enumerate(data):
            v = float(v - m) / M
            p = int(v * h)

            if color is None:
                c = int(v * 255)
                k = (255 - c, c, 0, 255)
            else:
                k = color

            self.pam.rect([
                (Z * i + 1, h - 1),
                (Z * i + Z - 1, h - p - 1),
            ], fill=k)

    def center_plot(self, data, color=None):
        w, h = self.size
        N = len(data)
        m = min(data)
        M = max(max(data), abs(m))
        Z = self.Z

        base = h / 2

        for i, v in enumerate(data):
            v = float(v) / M / 2
            p = int(v * h)
            c = int((v + .5) * 255)

            self.pam.rect([
                (Z * i + 1, h - 1 - base),
                (Z * i + Z - 1, h - 1 - p - base),
            ], fill=(255 - c, c, 0, 255))

    def output(self):
        sys.stdout.write("\x1b]1337;File=inline=1:%s\a" % (
            base64.b64encode(self.pam.as_string()),
        ))
        sys.stdout.flush()

def main():
    N=100
    #dat = [i for i in xrange(N)]
    dat = [random.random() * 2 - 1 for i in xrange(N)]
    #dat = [(i - 50.) / 100 for i in xrange(N)]

    plt = Plot(N, Z=5, rows=1)
    #plt.line_plot(dat)
    #plt.bar_plot(dat)
    plt.center_plot(dat)
    plt.output()

    print ''

#import cStringIO, cProfile, pstats
#pr = cProfile.Profile()
#pr.enable()
main()
#pr.disable()
#s = cStringIO.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print s.getvalue()

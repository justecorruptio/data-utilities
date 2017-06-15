#!/usr/bin/env python -S -u

import argparse
import os, sys, tty, termios, re
import base64
import random
from struct import pack


def get_cell_size():
    fh = open('/dev/tty', 'rw')
    fd = fh.fileno()

    termios.tcflush(fd, termios.TCIOFLUSH)
    term_attr = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    sys.stdout.write("\x1b]1337;ReportCellSize\a")
    sys.stdout.flush()

    b = ''
    while True:
        b += fh.read(1)
        match = re.search(r'(\d+\.\d);(\d+\.\d)', b)
        if match:
            c_h, c_w = match.groups()
            break

    termios.tcsetattr(fd, termios.TCSANOW, term_attr)

    return float(c_w), float(c_h)


def get_window_size():
    c_w, c_h = get_cell_size()
    h, w = os.popen('stty size').read().split()
    return int(int(w) * c_w), int(int(h) * c_h)


class PAM(object):
    def __init__(self, size):
        self.w, self.h = size

        self.data = [(0, 0, 0, 0)] * (self.w * self.h)

    def rect(self, pos, fill=(255, 0, 0, 255)):
        (a, b), (c, d) = pos
        if c < a:
            a, c = c, a
        if d < b:
            b, d = d, b

        for i in xrange(a, c + 1):
            for j in xrange(b, d + 1):
                self.data[j * self.w + i] = fill

    def line(self, pos, fill=(255, 0, 0, 255)):
        (a, b), (c, d) = pos
        dx = c - a
        dy = d - b

        steep = abs(dy) > abs(dx)
        if steep:
            a, b = b, a
            c, d = d, c

        swapped = False
        if a > c:
            a, c = c, a
            b, d = d, b

        dx = c - a
        dy = d - b

        err = int(dx / 2.0)
        s = 1 if b < d else -1

        j = b
        for i in xrange(a, c + 1):
            if steep:
                self.data[i * self.w + j] = fill
            else:
                self.data[j * self.w + i] = fill
            err -= abs(dy)
            if err < 0:
                j += s
                err += dx

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
        self.N = N
        self.Z = Z

        c_w, c_h = map(int, get_cell_size())
        self.cell_size = (c_w, c_h)
        self.size = (self.Z * self.N, rows * c_h)
        self.rows = rows
        self.cols = (self.size[0] - 1) / c_w + 1

        self.clear()

    def clear(self):
        self.pam = PAM(self.size)

    def line_plot(self, data, color=(0, 255, 255, 255)):
        w, h = self.size
        N = len(data)
        m = min(data)
        M = max(data) - m
        Z = self.Z

        line = [
            (Z * i, h - 1 - (
                int(float(v - m) / M * (h - 1)) if M else 0
            ))
            for i, v in enumerate(data)
        ]
        for i in xrange(1, len(line)):
            self.pam.line([line[i - 1], line[i]], fill=color)

    def bar_plot(self, data, color=None):
        w, h = self.size
        N = len(data)
        m = min(data)
        M = max(data) - m
        Z = self.Z

        for i, v in enumerate(data):
            if M:
                v = float(v - m) / M
            else:
                v = 0
            p = int(v * (h - 1))

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
            if M:
                v = float(v) / M / 2
            else:
                v = 0
            p = int(v * (h - 1))
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
        sys.stdout.write('\b')
        sys.stdout.flush()

    def wipe(self):
        if self.rows > 1:
            sys.stdout.write('\x1b[%dA' % (self.rows - 1,))
        sys.stdout.write('\x1b[%dD' % (self.cols,))
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description='iTerm2 sparkline')
    parser.add_argument('--num', '-n', type=int, help='samples to show', default=None)
    parser.add_argument('--width', '-w', type=int, help='sample width in pixels', default=5)
    parser.add_argument('--type', '-t', type=str, help='bar, center, or line', default='line')
    parser.add_argument('--rows', '-r', type=int, help='height in rows', default=1)
    parser.add_argument('--flow', '-f', help='like tail -f', default=False, action='store_true')

    args = parser.parse_args()

    if not args.flow:
        data = [
            int(x)
            for x in sys.stdin.read().split('\n')
            if x
        ]
        if args.num is None:
            args.num = len(data)

        plot = Plot(args.num, Z=args.width, rows=args.rows)
        getattr(plot, args.type + '_plot')(data)
        plot.output()
        print ''
    else:
        args.num = args.num or 100
        data = [0] * args.num

        plot = Plot(args.num, Z=args.width, rows=args.rows)
        while True:
            getattr(plot, args.type + '_plot')(data)
            plot.output()
            try:
                line = next(sys.stdin)
            except StopIteration:
                break
            sample = float(line.strip())
            data.pop(0)
            data.append(sample)
            plot.wipe()
            plot.clear()

if __name__ == '__main__':
    main()

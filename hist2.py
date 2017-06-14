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
    def __init__(self, data, Z=3):
        self.w, self.h = map(int, get_cell_size())
        self.Z = Z
        self.N = len(data)
        self.M = max(data)
        self.data = data

        self.img = Image.new('RGBA', (self.Z * self.N, self.h))

    def line_plot(self):
        line = [
            (self.Z * i, self.h - int(float(v) / self.M * self.h) - 1)
            for i, v in enumerate(self.data)
        ]
        draw = ImageDraw.Draw(self.img)
        draw.line(line, fill=(255, 0, 0, 255))

    def bar_plot(self):
        draw = ImageDraw.Draw(self.img)
        for i, v in enumerate(self.data):
            v = float(v) / self.M
            p = int(v * self.h)
            c = int(v * 255)

            draw.rectangle([
                (self.Z * i, self.h - 1),
                (self.Z * i + self.Z - 2, self.h - p - 1),
            ], fill=(255 - c, c, 0, 255))

    def output(self):
        buff = StringIO.StringIO()
        self.img.save(buff, format='PNG')

        sys.stdout.write('[')
        sys.stdout.flush()
        sys.stdout.write("\x1b]1337;File=inline=1:%s\a" % (
            base64.b64encode(buff.getvalue()),
        ))
        sys.stdout.write('\b]\n')
        sys.stdout.flush()


import random

plt = Plot([random.randint(0, 100) for i in xrange(100)])
#plt.line_plot()
plt.bar_plot()
plt.output()

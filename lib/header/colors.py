"""ANSI escape sequence objects.

This is designed to place ANSI escape sequences in format strings.
Colors and attributes are selected by using object attributes in
format strings.

For example,

    '{0.red}Hello, {0.green}World!{0.reset}'.format(colors())

This prints "Hello, " in red, and "World" in green, and resets the
color so it doesn't spill onto the next line.  You can chain
attributes:

    '{0.red.underline}Red, underline{0.reset}'.format(colors())

Colors will also be disabled if stdout is not a tty.  If you want to
print to a different file descriptor, you can specify that file
instead, as an argument:

    fp.write('{0.red}Hello{0.reset}\n'.format(colors(fp)))

"""
import sys

class ANSIColor(object):
    reset = 0

    bold = 1
    italics = 3
    underline = 4
    inverse = 7
    strikethrough = 9

    nobold = 22
    noitalics = 23
    nounderline = 24
    noinverse = 27
    nostrikethrough = 29

    black = 30
    red = 31
    green = 32
    yellow = 33
    blue = 34
    magenta = 35
    cyan = 36
    white = 37
    default = 39

    bg_black = 40
    bg_red = 41
    bg_green = 42
    bg_yellow = 43
    bg_blue = 44
    bg_magenta = 45
    bg_cyan = 46
    bg_white = 47
    bg_default = 49

class _ANSIColors(object):
    __slots__ = ['_colors']
    def __init__(self, colors):
        self._colors = tuple(colors)
    def __getattr__(self, attr):
        value = getattr(ANSIColor, attr)
        return _ANSIColors(self._colors + (value,))
    def __str__(self):
        return '\x1b[{}m'.format(';'.join([str(c) for c in self._colors]))
    def __repr__(self):
        return '_Colors({!r})'.format(self._colors)

class _NoColors(object):
    __slots__ = []
    def __getattr__(self, attr):
        getattr(ANSIColor, attr)
        return self
    def __str__(self):
        return ''
    def __repr__(self):
        return '_NoColors()'

def colors(fp=None):
    if fp is None:
        fp = sys.stdout
    if fp.isatty():
        return _ANSIColors(())
    return _NoColors()

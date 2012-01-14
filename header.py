#! /usr/bin/env python
# Insert guards in all header files, if they don't exist.
# Fix the guards if they are incorrect.
import os
import sys
import stat
import re
import optparse
import fnmatch
import subprocess
import json
import datetime
import ConfigParser
try:
    import readline
except ImportError:
    pass

# Tracks warnings for display at end
toolong = []

ISTTY = sys.stdout.isatty()

GITCONFIG = None
def get_gitconfig():
    global GITCONFIG
    if GITCONFIG is None:
        c = ConfigParser.ConfigParser()
        c.read(os.path.join(os.getenv('HOME'), '.gitconfig'))
        GITCONFIG = c
    return GITCONFIG

def ask(what, default):
    if default is None:
        prompt = '%s: ' % what
    else:
        prompt = '%s [%s]: ' % (what, default)
    while True:
        try:
            answer = raw_input(prompt)
        except KeyboardInterrupt:
            print
            raise
        except EOFError:
            print
            sys.exit(1)
        answer = answer.strip()
        if answer:
            return answer
        elif default is not None:
            return default

COPYRIGHT = { }
def get_copyright(opts):
    c = COPYRIGHT
    try:
        return c['message']
    except KeyError:
        pass

    try:
        year = c['year']
    except KeyError:
        year = datetime.date.today().year
        c['year'] = year

    try:
        author = c['author']
    except KeyError:
        try:
            name = opts.name
        except AttributeError:
            name = None
        if name is None:
            try:
                name = get_gitconfig().get('user', 'name')
            except ConfigParser.NoOptionError:
                name = None
            name = ask('Author name (for copyright)', name)

        try:
            email = opts.email
        except AttributeError:
            email = None
        if email is None:
            try:
                email = get_gitconfig().get('user', 'email')
            except ConfigParser.NoOptionError:
                email = None
            email = ask('Email address (for copyright)', email)

        author = '%s <%s>' % (name, email)

    message = ['/* Copyright %d %s\n' % (year, author),
               '   See LICENSE.txt for details.  */\n']
    c['message'] = message

    return message

def hilite(string):
    if not ISTTY:
        return string
    attr = ['31', '1']
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)

class AbsPattern(object):
    def __init__(self, parts):
        self.parts = parts
    def matchdir(self, name):
        if not fnmatch.fnmatch(name, self.parts[0]):
            return False
        if len(self.parts) == 1:
            return True
        return AbsPattern(self.parts[1:])
    def matchfile(self, name):
        return len(self.parts) == 1 and \
            fnmatch.fnmatch(name, self.parts[0])
    def __str__(self):
        return '/' + '/'.join(self.parts)

class RelPattern(object):
    def __init__(self, pat):
        self.pat = pat
    def matchdir(self, name):
        if not fnmatch.fnmatch(name, self.pat):
            return self
        return True
    def matchfile(self, name):
        return fnmatch.fnmatch(name, self.pat)
    def __str__(self):
        return self.pat

class PatternSet(object):
    def __init__(self, pats=[]):
        self.pats = pats
    def matchdir(self, name):
        pats = []
        result = True
        for neg, dironly, pat in self.pats:
            r = pat.matchdir(name)
            if isinstance(r, bool):
                if r:
                    result = neg
            else:
                pats.append((neg, dironly, r))
        if not result:
            return False
        else:
            return PatternSet(pats)
    def matchfile(self, name):
        result = True
        for neg, dironly, pat in self.pats:
            if not dironly and result != neg and pat.matchfile(name):
                result = neg
        return result
    def add_pats(self, pats):
        """Make a new PatternSet with additional patterns."""
        npats = []
        for pat in pats:
            if pat.startswith('!'):
                neg = True
                pat = pat[1:]
                if not pat:
                    continue
            else:
                neg = False
            if pat.endswith('/'):
                dironly = True
                pat = pat[:-1]
            else:
                dironly = False
            if '/' in pat:
                parts = [p for p in pat.split('/') if p]
                pat = AbsPattern(parts)
            else:
                pat = RelPattern(pat)
            npats.append((neg, dironly, pat))
        if npats:
            return PatternSet(self.pats + npats)
        else:
            return self
    def read(self, path):
        """Make a new PatternSet with additional patterns from a file."""
        try:
            f = open(path, 'r')
        except OSError:
            return self
        try:
            npats = []
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                npats.append(line)
        finally:
            f.close()
        return self.add_pats(npats)
    def dump(self):
        print 'Patterns:'
        for neg, dironly, pat in self.pats:
            r = ''
            if neg:
                r += '!'
            r += str(pat)
            if dironly:
                r += '(dir only)'
            print '    ', r

EXTS = set(['.h', '.hpp', '.m', '.mm', '.cpp', '.c'])

nontok = re.compile('[^a-zA-Z0-9]+')

def fread(path):
    f = open(path, 'r')
    try:
        return list(f)
    finally:
        f.close()

def fwrite(path, text):
    f = open(path, 'w')
    try:
        f.write(text);
    finally:
        f.close()

def prompt(p):
    while True:
        try:
            answer = raw_input(p + ' ')
        except KeyboardInterrupt:
            print
            raise
        except EOFError:
            print
            sys.exit(1)
        if answer.lower().startswith('y'):
            return True
        elif answer.lower().startswith('n'):
            return False
        print "Can't understand answer %r" % answer

class Proxy(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return '<Proxy %r>' % self.name

class ChainDict(object):
    """Dictionary type which can 'inherit' from parent dictionaries."""
    _unset = Proxy("unset")
    def __init__(self, parent=None):
        self._parent = parent
    def __getattribute__(self, key):
        if key.startswith('_'):
            return object.__getattribute__(self, key)
        try:
            val = object.__getattribute__(self, key)
        except AttributeError:
            pass
        else:
            if val is ChainDict._unset:
                raise AttributeError(key)
            return val
        return getattr(object.__getattribute__(self, '_parent'), key)
    def __delattr__(self, key):
        object.__setattr__(self, ChainDict._unset)

DIRECTIVE = re.compile('#\s*(\w+)')

def split_directives(text, directives):
    """Split text (list of lines) into two arrays.

    The first array is the longest one containing only valid C or C++
    style comments and directives from the given set, which can be
    empty.
    """
    extent = 0
    pos = 0
    end = len(text)
    while True:
        if pos >= end:
            break
        l = text[pos].strip()
        while l.startswith('/*'):
            l = l[2:]
            while True:
                i = l.find('*/')
                if i >= 0:
                    l = l[i+2:].strip()
                    break
                pos += 1
                if pos >= end:
                    l = ''
                    break
                l = text[pos]
        if l.startswith('//') or not l:
            pos += 1
            extent = pos
            continue
        if directives:
            m = DIRECTIVE.match(l)
            if m and m.group(1) in directives:
                pos += 1
                extent = pos
                continue
        break
    return text[:extent], text[extent:]

EXTERNC = re.compile('extern\s*"C"');
EXTERNC_PRE = [
    '#ifdef __cplusplus\n',
    'extern "C" {\n',
    '#endif\n',
]
EXTERNC_POST = [
    '#ifdef __cplusplus\n',
    '}\n',
    '#endif\n',
]

def scan_file(opts, relpath):
    base, ext = os.path.splitext(relpath)
    abspath = os.path.join(opts.root, relpath)
    if ext not in EXTS:
        return

    is_header = ext in ('.h', '.hpp')
    is_c_header = ext == '.h'

    # Calculate header guard name
    gn = None
    if is_header and opts.guards:
        guard_root = opts.guard_root
        assert relpath.startswith(guard_root)
        if guard_root:
            gn = relpath[len(guard_root) + 1:]
        else:
            gn = relpath
        gn = nontok.subn('_', opts.guard_prefix + gn)[0].upper()
    text = fread(abspath)
    otext = text[:]

    # Detabify, remove trailing space, remove double blank lines,
    # remove trailing blank lines, ensure trailing newline
    if opts.whitespace:
        tabsize = opts.tabsize
        blank = False
        ntext = []
        for line in text:
            line = line.expandtabs(tabsize).rstrip()
            if line:
                if blank:
                    ntext.append('\n')
                ntext.append(line + '\n')
                blank = False
            else:
                blank = True
        text = ntext

    # Remove first comment
    head1, text = split_directives(text, ())

    # Check for copyright notice
    if opts.copyright:
        for line in head1:
            if 'copyright' in line.lower():
                break
        else:
            head1 = get_copyright(opts) + head1

    if is_header:
        # Remove old header guard
        if len(text) >= 3:
            if text[0].startswith('#ifndef') and \
                    text[1].startswith('#define') and \
                    text[-1].startswith('#endif'):
                text = text[2:-1]

        if is_c_header and opts.externc:
            # Check for existence of 'extern "C"' anywhere in the file
            # If it exists, don't mess with it
            for line in text:
                if EXTERNC.match(line):
                    break
            else:
                # Remove next comment, with '#include' / '#import'
                head2, text = split_directives(text, ('include', 'import'))

                # Add 'extern "C"'
                text = head2 + EXTERNC_PRE + text + EXTERNC_POST

        # Add new header guard
        if gn:
            guard_pre = [
                '#ifndef ' + gn + '\n',
                '#define ' + gn + '\n',
            ]
            guard_post = [
                '#endif\n'
            ]
            text = guard_pre + text + guard_post
    else:
        # Not a header
        if opts.configh:
            for line in text:
                if (line.startswith('#') and
                    'include' in line and
                    'config.h' in line):
                    break;
            else:
                iconfig = [
                    '#ifdef HAVE_CONFIG_H\n',
                    '#include "config.h"\n',
                    '#endif\n',
                ]
                text = iconfig + text

    # Add comments back
    text = head1 + text

    # Ask user if changes are acceptable
    if otext != text:
        text = ''.join(text)
        print hilite('===== %s =====' % relpath)
        if not opts.no_diff:
            proc = subprocess.Popen(['diff', '-u', '--', abspath, '-'],
                                    stdin=subprocess.PIPE)
            proc.communicate(text)
        if not opts.no_action:
            if opts.yes or prompt('apply changes?'):
                fwrite(abspath, text)

    # Check line width
    width = opts.width
    if width > 0:
        for n, line in enumerate(text):
            columns = len(line.rstrip())
            if columns > width:
                toolong.append((relpath, n + 1, columns))

class SettingError(Exception):
    pass

def set_guard_prefix(opts, value, dirpath):
    if not isinstance(value, basestring):
        raise SettingError("guard_prefix must be a string")
    opts.guard_prefix = value
    opts.guard_root = dirpath

def set_ignore(opts, value, dirpath):
    if not isinstance(value, list):
        if isinstance(value, basestring):
            value = [value]
        else:
            raise SettingError("ignore must be a string or list of strings")
    else:
        for v in value:
            if not isinstance(v, basestring):
                raise SettingError(
                    "ignore must be a string or list of strings")
    opts.filter = opts.filter.add_pats(value)

def set_guards(opts, value, dirpath):
    if not isinstance(value, bool):
        raise SettingError("guards must be a boolean")
    opts.guards = value

def set_width(opts, value, dirpath):
    if not isinstance(value, int):
        raise SettingError("width must be integer")
    opts.width = value

def set_tabsize(opts, value, dirpath):
    if not (isinstance(value, int) and 1 < value < 8):
        raise SettingError("tabsize must be integer between 1 and 8")
    opts.tabsize = value

def set_externc(opts, value, dirpath):
    if not isinstance(value, bool):
        raise SettingError("externc must be a boolean")
    opts.externc = value

def set_configh(opts, value, dirpath):
    if not isinstance(value, bool):
        raise SettingError("configh must be a boolean")
    opts.configh = value

SETKEYS = {
    'guard_prefix': set_guard_prefix,
    'ignore': set_ignore,
    'guards': set_guards,
    'width': set_width,
    'tabsize': set_tabsize,
    'extern_c': set_externc,
    'configh': set_configh,
}

def read_settings(opts, abspath, dirpath):
    try:
        data = json.load(open(abspath, 'rb'))
        for key, value in data.iteritems():
            try:
                setter = SETKEYS[key]
            except KeyError:
                raise SettingError("unknown setting %r" % key)
            setter(opts, value, dirpath)
    except (ValueError, SettingError) as ex:
        print >> sys.stderr, "%s: %s" % (
            os.path.join(dirpath, '.header'), ex)
        sys.exit(1)

def scan_dir(opts, relpath):
    root = opts.root
    abspath = os.path.join(root, relpath)

    fnames = list(os.listdir(abspath))
    fnames.sort()
    if '.git' in fnames and relpath:
        print 'Skipping separate repository %r' % relpath
        return

    if '.gitignore' in fnames:
        ignore = os.path.join(abspath, '.gitignore')
        opts.filter = opts.filter.read(ignore)

    if '.header' in fnames:
        read_settings(opts, os.path.join(abspath, '.header'), relpath)

    filter = opts.filter
    for fname in fnames:
        if fname.startswith('.'):
            continue
        frelpath = os.path.join(relpath, fname)
        fabspath = os.path.join(abspath, fname)
        s = os.stat(fabspath)
        if stat.S_ISDIR(s.st_mode):
            subfilter = filter.matchdir(fname)
            if not subfilter:
                if opts.verbose:
                    print 'Skipping %r' % frelpath
            else:
                subopts = ChainDict(opts)
                subopts.filter = subfilter
                scan_dir(subopts, frelpath)
        elif stat.S_ISREG(s.st_mode):
            if filter.matchfile(fname):
                scan_file(opts, frelpath)
            else:
                if opts.verbose:
                    print 'Skipping %r' % frelpath

def run():
    parser = optparse.OptionParser()
    parser.add_option('--user', dest='user',
                      help='user name for copyright notice',
                      action='store', default=None)
    parser.add_option('--email', dest='email',
                      help='email address for copyright notice',
                      action='store', default=None)
    parser.add_option('-s', '--strip-copyright', dest='strip',
                      help='strip copyright notices', action='store_true',
                      default=False)
    parser.add_option('-i', '--ignore', dest='ignore',
                      help='ignore objects matching patterns',
                      action='append', default=[])
    parser.add_option('-y', '--yes', dest='yes',
                      help='do not ask before applying changes',
                      action='store_true', default=False)
    parser.add_option('-n', '--no-action', dest='no_action',
                      help='do not apply any changes',
                      action='store_true', default=False)
    parser.add_option('-v', '--verbose', dest='verbose',
                      help='verbose output',
                      action='store_true', default=False)
    parser.add_option('--no-diff', dest='no_diff',
                      help='suppress diff',
                      action='store_true', default=False)
    parser.add_option('-t', '--tabsize', dest='tabsize',
                      help='set tabsize, default 8',
                      action='store', type='int', default=8)
    parser.add_option('-w', '--whitespace', dest='whitespace',
                      help='fix whitespace issues',
                      action='store_true', default=False)
    parser.add_option('--width', dest='width',
                      help='check width',
                      action='store', default=0, type='int')
    parser.add_option('-c', '--configh', dest='configh',
                      help='include "config.h" from C/C++ files',
                      action='store_true', default=False)
    parser.add_option('--no-copyright', dest='copyright',
                      help="don't add copyright message",
                      action='store_false', default=True)
    (options, args) = parser.parse_args()
    ignore = []
    for opt in options.ignore:
        ignore.extend(opt.split(','))
    filter = PatternSet().add_pats(ignore)
    for arg in args or ['.']:
        opts = ChainDict(options)
        opts.root = os.path.abspath(arg)
        opts.guard_root = ''
        opts.guard_prefix = ''
        opts.guards = True
        opts.externc = False
        opts.filter = filter
        scan_dir(opts, '')
    if toolong:
        print hilite('===== Lines too long =====')
        for path, lineno, width in toolong:
            print '%s:%i: %d columns wide' % (path, lineno, width)

try:
    run()
except KeyboardInterrupt:
    pass

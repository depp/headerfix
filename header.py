#! /usr/bin/env python
# Insert guards in all header files, if they don't exist.
# Fix the guards if they are incorrect.
import os
import sys
import stat
import re
import optparse
import fnmatch
try:
    import readline
except ImportError:
    pass

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
        for line in text:
            f.write(line)
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

def scan_file(fabs, frel, options):
    base, ext = os.path.splitext(fabs)
    if ext not in EXTS:
        return
    gn = None
    if (ext == '.h' and
        not os.path.isfile(base + '.m') and
        not os.path.isfile(base + '.mm')):
        if frel.startswith('include/'):
            gn = frel[len('include/'):]
        else:
            gn = frel
        gn = nontok.subn('_', gn)[0].upper()
    text = fread(fabs)
    ohead = []
    otail = []
    if options.strip:
        if '/*' in text[0] >= 0:
            while True:
                l = text.pop(0)
                ohead.append(l)
                if '*/' in l:
                    break
    if gn:
        nhead = ['#ifndef ' + gn + '\n', '#define ' + gn + '\n']
        ntail = ['#endif\n']
    else:
        nhead = []
        ntail = []
    if len(text) >= 3:
        if text[0].startswith('#ifndef') and \
                text[1].startswith('#define') and \
                text[-1].startswith('#endif'):
            if text[:2] == nhead and text[-1:] == ntail:
                nhead = []
                ntail = []
            else:
                ohead.extend(text[:2])
                otail = [text[-1]]
                text = text[2:-1]
    if not nhead and not ntail and not ohead and not otail:
        return
    print frel
    if not options.no_diff:
        print 'Old version:'
        for line in ohead + ['<<body>>\n'] + otail:
            print '    ' + line,
        print 'New version:'
        for line in nhead + ['<<body>>\n'] + ntail:
            print '    ' + line,
    if not options.no_action:
        if options.yes or prompt('apply changes?'):
            fwrite(fabs, nhead + text + ntail)

def scan_dir(rootabs, rootrel, options, filter):
    fnames = list(os.listdir(rootabs))
    if '.git' in fnames and rootrel:
        print 'Skipping separate repository %r' % rootrel
        return
    if '.gitignore' in fnames:
        filter = filter.read(rootabs + '/.gitignore')
    for fname in os.listdir(rootabs):
        frel = rootrel + fname
        if fname.startswith('.'):
            continue
        fabs = rootabs + '/' + fname
        s = os.stat(fabs)
        if stat.S_ISDIR(s.st_mode):
            filter2 = filter.matchdir(fname)
            frel += '/'
            if filter2:
                scan_dir(fabs, frel, options, filter2)
            else:
                if options.verbose:
                    print 'Skipping %r' % frel
        elif stat.S_ISREG(s.st_mode):
            if filter.matchfile(fname):
                scan_file(fabs, frel, options)
            else:
                if options.verbose:
                    print 'Skipping %r' % frel

def run():
    parser = optparse.OptionParser()
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
    (options, args) = parser.parse_args()
    ignore = []
    for opt in options.ignore:
        ignore.extend(opt.split(','))
    filter = PatternSet().add_pats(ignore)
    for arg in args or ['.']:
        scan_dir(arg, '', options, filter)

try:
    run()
except KeyboardInterrupt:
    pass

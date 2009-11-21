# Header Fixer - fixheader.py
# Copyright 2007 - 2009 Dietrich Epp <depp@zdome.net>
# This source code is licensed under the GNU General Public License,
# Version 3. See gpl-3.0.txt for details.
import re
import os
import datetime
import sys
import subprocess
# Simply loading the readline module gives us editing capabilities
# when calling raw_input().  It's not necessary, so we ignore
# exceptions when importing it.
try:
    import readline
except ImportError:
    pass

def eval_cmd(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    if proc.returncode == 0:
        return out
    return None

def get_author_name():
    name = eval_cmd(['git', 'config', '--get', 'user.name'])
    email = eval_cmd(['git', 'config', '--get', 'user.email'])
    if name and email:
        return '%s <%s>' % (name, email)
    elif name:
        return name
    elif email:
        return '<%s>' % email
    return None

this_year = datetime.date.today().year

exclude_re = re.compile(r'(?:.*/)?(?:[.#][^/]*|[^/]*~)$')

def ask(question):
    question = '%s (y/n)? ' % question
    while 1:
        answer = raw_input(question)
        if answer.lower().startswith('y'):
            return True
        elif answer.lower().startswith('n'):
            return False
        print("don't understand answer %r" % answer)

class SkipHandler(object):
    def handle(self, obj, path):
        obj.note("skipping %r" % path)

class Handler(object):
    def apply_guard(self, obj, path, body):
        return body, False
    def apply_header(self, obj, path, body):
        htext, header = self.get_header(body)
        body = body[len(header):]
        new_htext = self.fix_header(obj, path, header)
        do_header = False
        if htext != new_htext:
            print('%s: current header' % path)
            for line in htext:
                line = line.rstrip('\n')
                print('  > ' + line)
            print('%s: new header' % path)
            for line in new_htext:
                line = line.rstrip('\n')
                print('  > ' + line)
            if ask('apply header'):
                do_header = True
            else:
                new_htext = htext
        body, do_guard = self.apply_guard(obj, path, body)
        return new_htext + body, do_guard or do_header
    def handle(self, obj, path):
        body, do_apply = self.apply_header(obj, path, list(open(path, 'r')))
        if do_apply:
            #tpath = path + '#header#'
            f = open(path, 'w')
            for line in body:
                f.write(line)
            f.close()
            #os.rename(tpath, path)
    def fix_header(self, obj, path, header):
        return obj.fix_header(path, header)

class GenHandler(Handler):
    def __init__(self, slcomment, mlcomment):
        self.slcomment = slcomment
        self.mlcomment = mlcomment
    def get_header(self, body):
        header = []
        htext = []
        if body:
            if self.slcomment and body[0].startswith(self.slcomment):
                for line in body:
                    if line.startswith(self.slcomment):
                        header.append(line[len(self.slcomment):].strip())
                        htext.append(line)
                    else:
                        break
            elif self.mlcomment:
                mlbegin, mlend = self.mlcomment
                if body[0].startswith(mlbegin):
                    for line in body:
                        htext.append(line)
                        if not header:
                            line = line[len(mlbegin):]
                        line = line.split(mlend, 1)
                        header.append(line[0].strip())
                        if len(line) == 2:
                            if line[1].strip():
                                raise Exception("Don't know what to do "
                                    "with text after comment.")
                            break
        return htext, header
    def comment(self, text):
        if not text:
            return text
        if self.mlcomment:
            begin, end = self.mlcomment
            for n, line in enumerate(text):
                if n:
                    prefix = ' ' * len(begin)
                else:
                    prefix = begin
                prefix = prefix + ' '
                if n < len(text) - 1:
                    suffix = ''
                else:
                    suffix = ' ' + end
                line = prefix + line + suffix + '\n'
                text[n] = line
        else:
            text = [self.slcomment + ' ' + line + '\n' for line in text]
        return text
    def fix_header(self, obj, path, header):
        h = super(GenHandler, self).fix_header(obj, path, header)
        return self.comment(h)

class PyHandler(GenHandler):
    def __init__(self):
        return GenHandler.__init__(self, '#', None)
    def fix_header(self, obj, path, header):
        if header and header[0].startswith('!'):
            h = super(PyHandler, self).fix_header(obj, path, header[1:])
            h = ['#' + header[0] + '\n'] + h
            return h
        else:
            return super(PyHandler, self).fix_header(obj, path, header)

class CHandler(GenHandler):
    def __init__(self, allowsl):
        if allowsl:
            sl = '//'
        else:
            sl = None
        GenHandler.__init__(self, sl, ('/*', '*/'))

class HeaderHandler(CHandler):
    def __init__(self, allowsl):
        CHandler.__init__(self, allowsl)
    def get_guard(self, body):
        start = 0
        end = len(body)
        if (end >= 2 and
                body[0].strip().startswith('#ifndef') and
                body[1].strip().startswith('#define')):
            start = 2
            while end > start:
                line = body[end - 1].strip()
                if line.startswith('#endif'):
                    end -= 1
                    break
                if not line:
                    end -= 1
                    continue
                else:
                    break
        return body[:start], body[start:end], body[end:]
    def apply_guard(self, obj, path, body):
        gstart, middle, gend = self.get_guard(body)
        gname = obj.header_guardname(path)
        mygstart = ['#ifndef %s\n' % gname, '#define %s\n' % gname]
        mygend = ['#endif\n']
        if mygstart != gstart or mygend != gend:
            print('%s: old guard' % path)
            for line in gstart + ['<<<BODY>>>'] + gend:
                line = line.rstrip('\n')
                print('  > %s' % line)
            print('%s: new guard' % path)
            for line in mygstart + ['<<<BODY>>>'] + mygend:
                line = line.rstrip('\n')
                print('  > %s' % line)
            if ask('apply'):
                do_apply = True
                body = mygstart + middle + mygend
            else:
                do_apply = False
        else:
            do_apply = False
        return body, do_apply

copy_re = re.compile(r'\s*Copyright\s*([-\d\s,]*\d)')
guard_re = re.compile(r'[^_A-Za-z0-9]+')
class HeaderFixer(object):
    def __init__(self):
        self.handlers = {}
    
    def note(self, str):
        if self.options.verbose:
            print(str)
    
    exts = {
        'c': 'c', # C
        'cpp': 'c', # C++
        'l': 'c', # Flex
        'm': 'c', # Objective-C
        'mm': 'c', # Objective-C++
        'h': 'h', # C Header
        'hpp': 'h', # C++ Header
        'py': 'py', # Python
        'rl': 'c', # Ragel
    }
    def makehandler_skip(self):
        return SkipHandler()
    def makehandler_c(self):
        return CHandler(True)
    def makehandler_h(self):
        return HeaderHandler(True)
    def makehandler_py(self):
        return PyHandler()
    def handler_ext(self, path, ext):
        return self.exts.get(ext, None)
    def handler_dotfile(self, path):
        return None
    def handler_name(self, path):
        root, filename = os.path.split(path)
        if filename.startswith('.'):
            return self.handler_dotfile(path)
        if not self.filter_path(path, False):
            return None
        base, ext = os.path.splitext(filename)
        if ext.startswith('.'):
            ext = ext[1:]
        return self.handler_ext(path, ext)
    def handler(self, path):
        name = self.handler_name(path) or 'skip'
        try:
            return self.handlers[name]
        except KeyError:
            try:
                h = getattr(self, "makehandler_%s" % name)
            except AttributeError:
                raise Exception("Unknown handler: %r" % name)
            h = h()
            self.handlers[name] = h
            return h
    
    def parse_years(self, text_years):
        years = set()
        for year_range in text_years.split(','):
            if '-' in year_range:
                start, end = tuple(year_range.split('-'))
                start = int(start)
                end = int(end)
                years.update(list(range(start, end + 1)))
            else:
                years.add(int(year_range))
        return years
    
    def update_years(self, path, years):
        pass
    
    def format_years(self, years):
        ranges = []
        for year in sorted(years):
            if ranges and ranges[-1][1] == year - 1:
                start, end = ranges.pop()
                end = year
            else:
                start, end = year, year
            ranges.append((start, end))
        range_texts = []
        for start, end in ranges:
            if end > start:
                range_texts.append('%s - %s' % (start, end))
            else:
                range_texts.append('%s' % start)
        return ', '.join(range_texts)
    
    def header_guardname(self, path):
        return guard_re.sub("_", path).upper()
    
    def find_copyright_dates(self, lines):
        for line in lines:
            match = copy_re.match(line)
            if match:
                return match.group(1)
        return None

    def default_date(self, path):
        return this_year
    
    def header_prefix(self, path):
        return ['%s - %s' % (self.project_name(path), path)]
    
    def header_copyright(self, path, dates):
        return ['Copyright %s %s' % (dates, self.project_author(path))]
    
    def gen_header(self, path, dates):
        header = []
        header.extend(self.header_prefix(path))
        header.extend(self.header_copyright(path, dates))
        header.extend(self.header_suffix(path))
        return header
    
    def fix_header(self, path, header):
        dates = self.find_copyright_dates(header)
        if not dates:
            dates = set([self.default_date(path)])
            print('No copyright found: %s' % path)
        else:
            dates = self.parse_years(dates)
        self.update_years(path, dates)
        dates = self.format_years(dates)
        return self.gen_header(path, dates)
    
    def process_dir(self, top):
        for root, dirnames, filenames in os.walk(top):
            root = os.path.normpath(root)
            dirnames[:] = [dirname for dirname in dirnames
                if self.filter_path(
                    os.path.normpath(os.path.join(root, dirname)), True)]
            for filename in filenames:
                path = os.path.normpath(os.path.join(root, filename))
                self.handler(path).handle(self, path)
    
    def run(self):
        try:
            from optparse import OptionParser
            parser = OptionParser()
            parser.add_option(
                "-d", "--update-dates", dest="update_dates",
                help="update copyright dates",
                action="store_true", default=False)
            parser.add_option(
                "-v", "--verbose", dest="verbose",
                help="verbose output", action="store_true", default=False)
            self.options, args = parser.parse_args()
            roots = args or ['.']
            roots = [os.path.normpath(root) for root in roots]
            for root in roots:
                if os.path.isabs(root):
                    raise Exception("Error: absolute path %r" % root)
                root = os.path.normpath(root)
                if os.path.isdir(root):
                    self.process_dir(root)
                else:
                    raise Exception("Can't process %r" % path)
        except KeyboardInterrupt:
            print
            sys.exit(1)

    def filter_path(self, path, isdir):
        if exclude_re.match(path):
            return False
        if path in getattr(self, "EXCLUDE", ()):
            return False
        return True
    def project_name(self, path):
        return self.PROJECT_NAME
    def header_suffix(self, path):
        return self.HEADER_SUFFIX
    HEADER_SUFFIX = []
    def project_author(self, path):
        return self.AUTHOR

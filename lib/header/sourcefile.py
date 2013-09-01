# Copyright 2013 Dietrich Epp.
#
# This file is part of HeaderFix.  HeaderFix is distributed under the terms of
# the 2-clause BSD license.  See LICENSE.txt for details.

import subprocess
from . import comment
from . import copyright

class SourceFile(object):
    __slots__ = ['path', 'relpath', 'env', 'filetype', 'lines',
                 'addspace_start', 'addspace_end']

    def __init__(self, path, relpath, env, filetype):
        self.path = path
        self.relpath = relpath
        self.env = env
        self.filetype = filetype
        with open(path, 'r') as fp:
            self.lines = fp.readlines()
        self.addspace_start = True
        self.addspace_end = True

    def run_filters(self):
        objs = []
        for filter in self.filters():
            filter1 = getattr(self, filter + '_filter1')
            filter2 = getattr(self, filter + '_filter2')
            obj = filter1()
            objs.append((filter2, obj))
        objs.reverse()
        for filter2, obj in objs:
            filter2(obj)

    def fix_whitespace(self):
        """Fix minor whitespace issues.

        Removes extra blank lines, trailing whitespace, and ensures
        that there is a line break at the end of the file.
        """
        lines = []
        blank = False
        for line in self.lines:
            line = line.rstrip()
            if line:
                if blank and lines:
                    lines.append('\n')
                lines.append(line + '\n')
                blank = False
            else:
                blank = True
        self.lines = lines

    def expand_tabs(self):
        """Convert tabs to spaces."""
        width = self.env['tabsize']
        self.lines = [line.expandtabs(width) for line in self.lines]

    def filters(self):
        yield 'shebang'
        if self.filetype.source:
            yield 'copyright'
        if self.filetype.name in ('h', 'hxx'):
            yield 'headerguard'
        if self.filetype.name == 'h' and self.env['extern_c']:
            yield 'externc'

    def write(self, fp):
        for line in self.lines:
            fp.write(line)

    def save(self):
        with open(self.path, 'w') as fp:
            self.write(fp)

    def diff(self):
        """Get the difference between the new text and the original.

        Returns None if there is no difference.
        """
        proc = subprocess.Popen(
            ['diff', '-u', '--', self.path, '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate(''.join(self.lines))
        if proc.returncode == 0:
            return None
        elif proc.returncode == 1:
            return stdout
        raise Exception('diff returned {}'.format(proc.returncode))

    def long_lines(self):
        """Enumerate (lineno,width) lines that are too long."""
        width = self.env['width']
        if width <= 0:
            return
        for lineno, line in enumerate(self.lines, 1):
            line = line.rstrip('\n')
            if len(line) > width:
                for exception in (): #('http://', 'https://', 'ftp://'):
                    if exception in line:
                        break
                else:
                    yield lineno, len(line)

    def wrap(self, head, tail, addspace_start, addspace_end):
        """Concatenate head and tail onto the beginning and end.

        If addspace_start is True and text is added to the beginning,
        then future non-zero starting text will get a line of padding.
        If addspace_end is true and text is added to the end, then
        future non-zero ending text will get a line of padding.
        """
        head = list(head or ())
        tail = list(tail or ())
        if (len(self.lines) < 2 and
            not any(line.strip() for line in self.lines) and
            (self.addspace_start or self.addspace_end) and
            head and tail):
            self.lines = ['\n'] * 2
        if head:
            if (self.addspace_start and
                self.lines and self.lines[0].strip()):
                head.append('\n')
            self.addspace_start = addspace_start
        if tail:
            if (self.addspace_end and
                self.lines and self.lines[-1].strip()):
                tail.insert(0, '\n')
            self.addspace_end = addspace_end
        if head or tail:
            self.lines = head + self.lines + tail

    def shebang_filter1(self):
        if not self.lines or not self.lines[0].startswith('#!'):
            return None
        return self.lines.pop(0)

    def shebang_filter2(self, shebang):
        if shebang is not None:
            self.wrap([shebang], None, False, False)

    def headerguard_filter1(self):
        head, body = comment.extract_lead_comments(self.lines, self.filetype)
        pre, body, post = comment.remove_blank_lines(body)
        if len(body) < 3:
            return None
        if (not body[0].startswith('#ifndef') or
            not body[1].startswith('#define') or
            not body[-1].startswith('#endif')):
            return None
        self.lines = body[2:-1]
        return head

    def headerguard_filter2(self, comments):
        head = list(comments or ())
        tail = []
        guardname = self.env['guardname']
        if self.env['guards'] and guardname:
            head.extend(['#ifndef {}\n'.format(guardname),
                         '#define {}\n'.format(guardname)])
            tail.append('#endif\n')
        self.wrap(head, tail, bool(comments), False)

    def copyright_filter1(self):
        head, body = comment.extract_lead_comment(self.lines, self.filetype)
        for pre, lbody, post in head:
            if 'COPYRIGHT' in lbody.upper():
                break
        else:
            return None
        self.lines = body
        return head

    def copyright_filter2(self, val):
        if not self.env['fix_copyright']:
            head = [pre + lbody + post for pre, lbody, post in val]
            self.lines = head + self.lines
            return
        if (self.filetype.linecomment is None and
            self.filetype.blockcomment is None):
            return
        authorship = copyright.Authorship()
        if val is not None:
            authorship.parse([line for pre, line, post in val])
        self.env['_authorship'].add_authorship(authorship)
        lines = authorship.dump()
        if self.env['copyright_notice']:
            for line in self.env['copyright_notice'].splitlines():
                lines.append(line + '\n')
        lines = comment.comment(lines, self.filetype, self.env['width'])
        if (self.filetype.blockcomment is None and
            self.lines and
            self.lines[0].strip().startswith(self.filetype.linecomment)):
            self.addspace_start = True
        else:
            self.addspace_start = False
        self.wrap(lines, None, False, False)

    def externc_filter1(self):
        return any('extern "C"' in line for line in self.lines)

    def externc_filter2(self, value):
        if value:
            return
        head = ['#ifdef __cplusplus\n',
                'extern "C" {\n',
                '#endif\n']
        tail = ['#ifdef __cplusplus\n',
                '}\n',
                '#endif\n']
        return self.wrap(head, tail, False, False)

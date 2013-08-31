import subprocess
import comment

class SourceFile(object):
    __slots__ = ['path', 'relpath', 'env', 'filetype', 'lines']

    def __init__(self, path, relpath, env, filetype):
        self.path = path
        self.relpath = relpath
        self.env = env
        self.filetype = filetype
        with open(path, 'r') as fp:
            self.lines = fp.readlines()

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
        yield 'copyright'
        if self.filetype.name in ('h', 'hxx'):
            yield 'headerguard'

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

    def shebang_filter1(self):
        if not self.lines or not self.lines[0].startswith('#!'):
            return None
        return self.lines.pop(0)

    def shebang_filter2(self, shebang):
        if shebang is not None:
            self.lines.insert(0, shebang)

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
        head = comments or []
        tail = []
        guardname = self.env['guardname']
        if self.env['guards'] and guardname:
            head.extend(['#ifndef {}\n'.format(guardname),
                         '#define {}\n'.format(guardname)])
            tail.append('#endif\n')
        if head or tail:
            self.lines = head + self.lines + tail

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
        if val is None:
            return
        head = [pre + lbody + post for pre, lbody, post in val]
        self.lines = head + self.lines

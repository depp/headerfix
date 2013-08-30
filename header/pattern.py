"""Patterns for matching file paths."""
import fnmatch

class GlobPattern(object):
    """A pattern that matches paths using globbing.

    The pattern can be rooted or unrooted.  Rooted patterns match
    against the beginning of the path, and unrooted patterns match
    against any part of the path.

    For example, the rooted pattern "/a/*" matches "/a/b" but not
    "/dir/a/b".  The unrooted pattern "a/*" matches both "/a/b" and
    "/dir/a/b".
    """
    __slots__ = ['rooted', 'parts']

    def __init__(self, rooted, parts):
        self.rooted = bool(rooted)
        self.parts = tuple(parts)
        assert self.parts

    def match_dir(self, name):
        """Apply the pattern against a directory.

        Returns (match, patterns), where "match" is true if the
        directory itself matches the pattern, and "patterns" is a set
        of patterns relative to the directory.
        """
        match = False
        patterns = []
        if fnmatch.fnmatch(name, self.parts[0]):
            if (len(self.parts) == 1 or
                (len(self.parts) == 2 and not self.parts[1])):
                match = True
            else:
                patterns.append(GlobPattern(True, self.parts[1:]))
        if not self.rooted:
            patterns.append(self)
        return match, patterns

    def match_file(self, name):
        """Determine whether this pattern matches a file."""
        return (len(self.parts) == 1 and
                fnmatch.fnmatch(name, self.parts[0]))

    def __str__(self):
        pat = '/'.join(self.parts)
        return '/' + pat if self.rooted else pat

    @classmethod
    def parse(class_, string):
        directory = string.endswith('/')
        rooted = string.startswith('/')
        parts = [part for part in string.split('/') if part]
        if directory:
            parts.append('')
        return class_(rooted, parts)

class PatternSet(object):
    """A set of positive and negative patterns."""
    __slots__ = ['patterns']

    def __init__(self, patterns=()):
        npatterns = []
        for positive, pattern in patterns:
            if npatterns or positive:
                npatterns.append((positive, pattern))
        self.patterns = tuple(npatterns)

    def __nonzero__(self):
        return bool(self.patterns)

    def match_dir(self, name):
        """Apply the pattern set against a directory.

        Returns (match, patternset), where "match" is true if the
        directory itself matches the pattern, and "patternset" is a
        new patternset relative to the directory.
        """
        dir_patterns = []
        dir_match = False
        for positive, pattern in self.patterns:
            pat_match, pat_patterns = pattern.match_dir(name)
            dir_patterns.extend(
                (positive, pat_pattern) for pat_pattern in pat_patterns)
            if match:
                dir_match = positive
        return dir_match, PatternSet(dir_patterns)

    def match_file(self, name):
        """Determine whether this pattern set matches a file."""
        result = False
        for positive, pattern in self.patterns:
            if result != positive and pattern.match_file(name):
                result = positive
        return result

    def union(self, other):
        """Compute the union of two PatternSet objects."""
        if not self.patterns:
            return other
        if not other.patterns:
            return self
        return PatternSet(self.patterns, other.patterns)

    @classmethod
    def parse(class_, strings):
        """Make a pattern set by parsing a list of strings as patterns."""
        patterns = []
        for string in strings:
            if string.startswith('!'):
                positive = False
                string = string[1:]
                if not string:
                    continue
            else:
                positive = True
            patterns.append((pasitive, GlobPattern.parse(string)))
        return class_(patterns)

    @classmethod
    def read(class_, fp):
        """Make a pattern set by parsing patterns from a file.

        This tries to use the same syntax as gitignore files.
        """
        patterns = []
        for line in fp:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            patterns.append(line)
        return class_(patterns)

    def dump(self):
        print 'Patterns:'
        for positive, pattern in self.patterns:
            print '    {}{}'.format('' if positive else '!', str(pattern))

    def match_path(self, path):
        """Test whether the pattern set matches a full path."""
        parts = [part for part in path.split('/') if part]
        if path.endswith('/'):
            fname = None
        else:
            parts, fname = parts[:-1], parts[-1]
        patternset = self
        for dirname in parts:
            match, patternset = patternset.match_dir(dirname)
            if match:
                return True
            if not patternset:
                return False
        if fname is not None:
            return patternset.match_file(fname)
        return False

if __name__ == '__main__':
    p = PatternSet.parse([
        'fname',
        '*.c',
        '!*.yy.c',
        'subdir/*.h',
        '!*.yy.h',
        '/rooted/x/y',
        'unrooted/x/y',
        '/rooted/x/*.py',
        'unrooted/x/*.py',
        'subdir/',
        '/rooted-subdir/',
    ])

    checks = [
        ('fname', True),
        ('abc.c', True),
        ('abc/def.c', True),
        ('abc.yy.c', False),
        ('abc/def.yy.c', False),
        ('fname/xyz', True),
        ('fname/abc.yy.c', True),

        ('rooted', False),
        ('rooted/x', False),
        ('rooted/x/y', True),
        ('rooted/x/z', False),
        ('rooted/x/file.py', True),
        ('rooted/x/y/z', True),

        ('a/rooted', False),
        ('a/rooted/x', False),
        ('a/rooted/x/y', False),
        ('a/rooted/x/z', False),
        ('a/rooted/x/file.py', False),
        ('a/rooted/x/y/z', False),

        ('subdir', False),
        ('subdir/', True),
        ('subdir/x', True),

        ('x/subdir', False),
        ('x/subdir/', True),
        ('x/subdir/x', True),

        ('rooted-subdir', False),
        ('rooted-subdir/', True),
        ('rooted-subdir/x', True),

        ('x/rooted-subdir', False),
        ('x/rooted-subdir/', False),
        ('x/rooted-subdir/x', False),
    ]
    for path, match in checks:
        if p.match_path(path) != match:
            raise Exception(
                'Expected match={} for path={}'.format(match, path))
    print 'Test passed'

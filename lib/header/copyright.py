import re
from . import git
from . import util
from . import year

YEARS = re.compile(r'\d(?:.*\d)?')
DIGIT = re.compile(r'\d')
EXTRA_SPACE = re.compile(r'\s\s+')

class Authorship(object):
    """Copyright authorship information."""
    __slots__ = ['authors']

    def __init__(self):
        self.authors = {}

    def __nonzero__(self):
        return bool(self.authors)

    def add_author(self, author, years):
        """Add an author with authorship for the given years."""
        author = author.strip()
        if not author.endswith('.'):
            author += '.'
        try:
            yearset = self.authors[author]
        except KeyError:
            yearset = set()
            self.authors[author] = yearset
        yearset.update(years)

    def parse(self, lines):
        """Parse authorship information from the given lines of text."""
        message = []
        groups = []
        group = None
        for line in lines:
            if 'COPYRIGHT' in line.upper():
                group = []
                groups.append(group)
            if group is not None:
                group.append(line)
                if line.rstrip().endswith('.') or not DIGIT.search(line):
                    group = None
        for group in groups:
            data = ' '.join(group)
            years = YEARS.search(data)
            if not years:
                raise ValueError('could not find copyright years')
            author = EXTRA_SPACE.sub(' ', data[years.end():])
            years = years.group(0)
            years = year.parse_years(years)
            self.add_author(author, years)

    def dump(self):
        """Get the authorship information as a list of lines."""
        authors = []
        for author, years in self.authors.iteritems():
            years = list(years)
            years.sort()
            authors.append((years, author))
        authors.sort()
        lines = []
        for years, author in authors:
            lines.append('Copyright {} {}\n'
                         .format(year.format_years(years), author))
        return lines

class AutoAuthorship(object):
    __slots__ = ['root', 'author', 'years']
    def __init__(self, root, author, years):
        self.root = root
        self.author = author
        self.years = years
    def add_authorship(self, authorship):
        if authorship:
            return
        if self.author is None:
            default = git.get_gitconfig('user', 'name')
            if default:
                author = util.ask('Author name [{}]:'.format(default), default)
            else:
                author = util.ask('Author name:')
            self.author = author
        if self.years is None:
            import datetime
            self.years = {datetime.date.today().year}
        authorship.add_author(self.author, self.years)

# Copyright 2013 Dietrich Epp.
#
# This file is part of HeaderFix.  HeaderFix is distributed under the terms of
# the 2-clause BSD license.  See LICENSE.txt for details.

import re

YEAR = re.compile(r'\d+')

def parse_years(years):
    """Parse a range of years as a set.

    For example, this will parse "1999-2001, 2007" as the set {1999,
    2000, 2001, 2007}.
    """
    yearset = set()
    lastyear = None
    lastpos = 0
    for match in YEAR.finditer(years):
        delim = years[lastpos:match.start()]
        lastpos = match.end()
        year = int(match.group())
        ndigits = len(match.group())
        if ndigits < 4:
            if lastyear is None or ndigits > 2:
                raise ValueError('year out of range: {}'.format(year))
            year = (lastyear // (10 ** ndigits)) * 10**ndigits + year
        if not (1900 <= year <= 3000):
            raise ValueError('year out of range: {}'.format(year))
        if '-' in delim:
            if lastyear is None or ',' in delim:
                raise ValueError('cannot parse year range: {}'.format(years))
            if year > lastyear:
                yearset.update(range(lastyear + 1, year + 1))
            else:
                raise ValueError(
                    'year range goes backwards: {}'.format(years))
            lastyear = None
        else:
            yearset.add(year)
            lastyear = year
    return yearset

def format_years(yearset):
    """Format a set of years.

    For example, this will format the set {1999, 2000, 2001, 2007} as
    "1999-2001, 2007".
    """
    yearlist = list(yearset)
    yearlist.sort()
    firstyear = None
    ranges = []
    for year in yearlist:
        if firstyear is None:
            firstyear = year
            lastyear = year
        elif year == lastyear + 1:
            lastyear = year
        else:
            ranges.append((firstyear, lastyear))
            firstyear = year
            lastyear = year
    if firstyear is not None:
        ranges.append((firstyear, lastyear))
    tranges = []
    for firstyear, lastyear in ranges:
        if firstyear < lastyear:
            tranges.append('{}-{}'.format(firstyear, lastyear))
        else:
            tranges.append(str(firstyear))
    return ', '.join(tranges)

if __name__ == '__main__':
    import sys
    def test(i, o):
        y = parse_years(i)
        x = format_years(y)
        if x != o:
            sys.stderr.write(
                'error: expected {!r}, got {!r}\n'
                '  years: {}\n'
                .format(o, x, ', '.join(str(year) for year in sorted(y))))
            sys.exit(0)
    test('1999', '1999')
    test('2000, 1, 2', '2000-2002')
    test('2000-10', '2000-2010')
    test('1999, 2000, 2001, 2008-2009', '1999-2001, 2008-2009')

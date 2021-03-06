# Copyright 2013 Dietrich Epp.
#
# This file is part of HeaderFix.  HeaderFix is distributed under the terms of
# the 2-clause BSD license.  See LICENSE.txt for details.

import argparse
import os
import subprocess
import sys
from . import rule
from . import scan
from . import pattern
from . import sourcefile
from . import filetype
from . import comment
from . import diff
from . import util
from . import copyright
from . import year
try:
    import readline
except ImportError:
    pass

def error(msg):
    print >>sys.stderr, 'error: {}'.format(msg)
    sys.exit(1)

def relpath_parts(path, base):
    parts = []
    curpath = path
    while curpath != base:
        lastpath = curpath
        curpath, fname = os.path.split(curpath)
        if lastpath == curpath:
            error('path not contained in repository: {}'.format(path))
        parts.append(fname)
    parts.reverse()
    return parts

def run(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--copyright-author',
        help='author name for copyright notice')
    parser.add_argument(
        '--copyright-years',
        type=year.parse_years,
        help='years for copyright authorship')
    parser.add_argument(
        '-s', '--strip-copyright',
        dest='strip', action='store_true', default=False,
        help='strip copyright notices',)
    parser.add_argument(
        '-i', '--ignore',
        dest='ignore', action='append', default=[],
        help='ignore objects matching patterns')
    parser.add_argument(
        '-y', '--yes',
        dest='yes', action='store_true', default=False,
        help='do not ask before applying changes')
    parser.add_argument(
        '-n', '--no-action',
        dest='no_action', action='store_true', default=False,
        help='do not apply any changes')
    parser.add_argument(
        '-v', '--verbose',
        dest='verbose', action='store_true', default=False,
        help='verbose output')
    parser.add_argument(
        '--no-diff', dest='no_diff',
        action='store_true', default=False,
        help='suppress diff')
    parser.add_argument(
        '-w', '--whitespace',
        dest='whitespace', action='store_true', default=False,
        help='fix whitespace issues')
    parser.add_argument(
        '--no-copyright',
        dest='copyright', action='store_false', default=True,
        help="don't add copyright message")
    parser.add_argument(
        '--rights',
        dest='rights', action='append', default=[],
        help="set the body of the copyright message")
    parser.add_argument(
        'path',
        nargs='*', default=['.'],
        help='scan the given paths')
    args = parser.parse_args()

    paths = [os.path.abspath(path) for path in args.path]
    root = paths[0]
    if not os.path.isdir(root):
        root = os.path.dirname(root)
        if not os.path.isdir(root):
            error('cannot find repository root: {}'.format(paths[0]))
    root = subprocess.check_output(
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=root)[:-1]
    paths = [relpath_parts(path, root) for path in paths]
    if all(paths):
        includes = pattern.PatternSet(
            (True, pattern.LiteralPattern(True, path)) for path in paths)
    else:
        includes = None

    excludes = pattern.PatternSet.parse(['.*'] + args.ignore)

    authorship = copyright.AutoAuthorship(
        root, args.copyright_author, args.copyright_years)
    rules = rule.Rules({'_authorship': authorship}, [])
    rules = rules.union(rule.Rules.read_global_gitignore())
    long_lines = []
    for path, env in scan.scan_dir(rules, root, includes, excludes):
        relpath = os.path.relpath(path)
        ftype = filetype.get_filetype(path)
        if ftype.name == 'unknown':
            continue
        src = sourcefile.SourceFile(path, relpath, env, ftype)

        src.run_filters()
        if args.whitespace:
            src.expand_tabs()
            src.fix_whitespace()
        flong_lines = list(src.long_lines())
        if flong_lines:
            long_lines.append((relpath, flong_lines))

        d = src.diff()
        if d is not None:
            if args.no_action:
                print
                print
                diff.show_diff(d)
            elif args.yes:
                print('Updating {}'.format(relpath))
                src.save()
            else:
                print
                print
                diff.show_diff(d)
                choice = util.ask(
                    'Apply changes to {} [y,n,q]?'.format(relpath),
                    None, ('Y', 'N', 'Q'))
                if choice == 'Q':
                    return
                if choice == 'Y':
                    src.save()

    if long_lines:
        for relpath, flong_lines in long_lines:
            print
            print '{}: Lines too long'.format(relpath)
            for lineno, width in flong_lines:
                print '    {}: {} columns'.format(lineno, width)

if __name__ == '__main__':
    import sys
    try:
        run(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(1)

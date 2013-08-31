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
from .colors import colors
try:
    import readline
except ImportError:
    pass

def error(msg):
    print >>sys.stderr, 'error: {}'.format(msg)
    sys.exit(1)

def ask(what, default):
    if default is None:
        prompt = what
    else:
        prompt = '{} [{}]'.format(what, default)
    prompt = '{0.bold.blue}{1}:{0.reset} '.format(colors(), prompt)
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
        '--user',
        help='user name for copyright notice')
    parser.add_argument(
        '--email',
        help='email address for copyright notice')
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

    if args.ignore:
        excludes = pattern.PatternSet.parse(args.ignore)
    else:
        excludes = None

    rules = rule.Rules({}, [])
    rules = rules.union(rule.Rules.read_global_gitignore())
    for path, env in scan.scan_dir(rules, root, includes, excludes):
        relpath = os.path.relpath(path)
        ftype = filetype.get_filetype(path)
        src = sourcefile.SourceFile(path, relpath, env, ftype)

        src.run_filters()
        src.show_diff()

if __name__ == '__main__':
    import sys
    try:
        run(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(1)

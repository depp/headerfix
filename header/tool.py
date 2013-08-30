import argparse
from . import rule
from . import scan

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

    rules = rule.Rules({}, [])
    #rules = rules.union(rule.read_global_gitignore())
    scan.scan_dir(rules, '.')

if __name__ == '__main__':
    import sys
    try:
        run(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(1)

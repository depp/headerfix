import os
from . import colors

def find_executable(name):
    """Find the path to an executable, or return None if not found."""
    for path in os.environ['PATH'].split(os.path.pathsep):
        if not path:
            continue
        epath = os.path.join(path, name)
        if os.path.exists(epath):
            return epath
    return None

def ask(what, default=None, choices=()):
    prompt = '{0.bold.blue}{1}{0.reset} '.format(colors.colors(), what)
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
            if choices:
                answer = answer.upper()
                if answer in choices:
                    return answer
            else:
                return answer
        elif default is not None:
            return default

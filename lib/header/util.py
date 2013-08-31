import os

def find_executable(name):
    """Find the path to an executable, or return None if not found."""
    for path in os.environ['PATH'].split(os.path.pathsep):
        if not path:
            continue
        epath = os.path.join(path, name)
        if os.path.exists(epath):
            return epath
    return None

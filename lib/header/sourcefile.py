class SourceFile(object):
    __slots__ = ['path', 'relpath', 'env', 'filetype', 'lines']

    def __init__(self, path, relpath, env, filetype):
        self.path = path
        self.relpath = relpath
        self.env = env
        self.filetype = filetype
        with open(path, 'r') as fp:
            self.lines = fp.readlines()

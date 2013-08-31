class BoolType(object):
    __slots__ = []
    def read(self, x):
        if x == "true":
            return True
        if x == "false":
            return False
        raise ValueError("expected true or false")
    def write(self, x):
        return "true" if x else "false"
    default = True

class IntType(object):
    __slots__ = ['minval', 'maxval']
    def __init__(self, minval, maxval):
        self.minval = minval
        self.maxval = maxval
    def read(self, x):
        v = int(x)
        if self.minval is not None and v < self.minval:
            raise ValueError(
                "value cannot be less than {}".format(self.minval))
        if self.maxval is not None and v > self.maxval:
            raise ValueError(
                "value cannot be more than {}".format(self.maxval))
        return v
    def write(self, x):
        return str(x)

class StringType(object):
    __slots__ = []
    def read(self, x):
        return x
    def write(self, x):
        return x

ENV_TYPES = {
    'ignore': BoolType(),
    'guardname': StringType(),
    'guards': BoolType(),
    'width': IntType(0, None),
    'tabsize': IntType(1, 8),
    'extern_c': BoolType(),
    'config_header': StringType(),
}

def parse_var(name, value):
    try:
        vartype = ENV_TYPES[name]
    except KeyError:
        raise ValueError('unknown variable: {!r}'.format(name))
    if value is None:
        try:
            return vartype.default
        except AttributeError:
            raise ValueError('missing value for {}'.format(name))
    else:
        try:
            return vartype.read(value)
        except ValueError as ex:
            raise ValueError('invalid value for {}: {}'.format(name, ex))

def dump_var(name, value):
    try:
        vartype = ENV_TYPES[name]
    except KeyError:
        raise ValueError('unknown variable: {!r}'.format(name))
    try:
        if value == vartype.default:
            return name
    except AttributeError:
        pass
    return '{} = {}'.format(name, vartype.write(value))

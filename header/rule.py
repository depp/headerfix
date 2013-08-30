from . import environ

DEFAULT_ENV = {
    'ignore': False,
    'guard_prefix': '',
    'guards': False,
    'width': 0,
    'tabsize': 4,
    'extern_c': False,
    'config_header': '',
}

class Lexer(object):
    __slots__ = ['fp', 'lineno']
    def __init__(self, fp):
        self.fp = fp
        self.lineno = 0
    def __iter__(self):
        return self
    def next(self):
        for line in self.fp:
            self.lineno += 1
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            fields = line.split()
            if fields[0] in ('{', '}'):
                if len(fields) != 1:
                    self.error('syntax error')
                return fields[0], None
            if fields[0] in ('+', '-'):
                if len(fields) != 2:
                    self.error('expected one pattern')
                return 'PATTERN', (fields[0] == '+',
                                   pattern.GlobPattern.parse(fields[1]))
            if len(fields) >= 2 and fields[1] == '=':
                if len(fields) == 3:
                    data = fields[2]
                elif len(fields) == 2:
                    data = ''
                else:
                    self.error('too many fields')
                name = fields[0]
                try:
                    return 'SET', (name, environ.parse_var(name, data))
                except ValueError as ex:
                    self.error(ex)
            if len(fields) == 1:
                try:
                    return 'SET', (name, environ.parse_var(name, None))
                except ValueError as ex:
                    self.error(ex)
            self.error('syntax error')
        raise StopIteration()
            
    def error(self, msg):
        raise ValueError('{}:{}: {}'.format(self.fp.name, self.lineno, msg))

class Rules(object):
    __slots__ = ['env', 'rules']

    def __init__(self, env, rules):
        e = dict(DEFAULT_ENV)
        e.update(env)
        self.env = e
        self.rules = tuple(rules)

    def __nonzero__(self):
        return bool(self.env) or bool(self.rules)

    def file_env(self, fname):
        """Get the environment for a file, or None if the file is ignored."""
        env = dict(self.env)
        for patternset, rule in self.rules:
            if patternset.match_file(fname):
                env.update(rule.env)
        if env['ignore']:
            return None
        return env

    def dir_rules(self, fname):
        """Get the rules for a directory, or None if it is ignored."""
        env = dict(self.env)
        rules = []
        for patternset, rule in self.rules:
            match, patternset = patternset.match_dir(fname)
            if patternset:
                rules.append((patternset, rule))
            if match:
                env.update(rule.env)
                rules.extend(rule.rules)
        if env['ignore']:
            return None
        return Rules(env, rules)

    def union(self, other):
        """Compute the union of two sets of rules."""
        e = dict(self.env)
        e.update(other.env)
        return Rules(e, self.rules + other.rules)

    @classmethod
    def _read_group(class_, lex):
        env = {}
        rules = []
        patterns = []
        for tok, data in lex:
            if tok == '{':
                rules.append(class_._read_group(lex))
            elif tok == '}':
                return pattern.PatternSet(patterns), class_(env, rules)
            elif tok == 'PATTERN':
                patterns.append(data)
            elif tok == 'SET':
                env[data[0]] = data[1]
            else:
                assert False
        lex.error('missing brace')

    @classmethod
    def read(class_, fp):
        """Read rules from a file."""
        env = {}
        rules = []
        lex = Lexer(fp)
        for tok, data in lex:
            if tok == '{':
                rules.append(class_._read_group(lex))
            elif tok == '}':
                lex.error('extra brace')
            elif tok == 'PATTERN':
                lex.error('unexpected pattern')
            elif tok == 'SET':
                env[data[0]] = data[1]
            else:
                assert False
        return class_(env, rules)
    

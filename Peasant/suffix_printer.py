
from sys import stderr,stdout

# Constants are convenient
DEF = DEFAULT = '[+]'
NOT = NOTICE  = '[-]'
WAR = WARNING = '[!]'

def suffix(s,suf=DEF):
    'Suffix a string with user-supplied input'

    return f'{suf} {s}'

def suffix_print(s, suf=DEF, sep='', file=stdout, end='\n'):
    'Print a string after suffixing it with user-supplied input'

    print(suffix(s, suf=suf), sep=sep, file=file, end=end)

def error_suffix_print(s, suf=DEF, sep='', end='\n'):

    suffix_print(s, suf=suf, sep=sep, file=stderr, end=end)

sprint = suffix_print
esprint = error_suffix_print

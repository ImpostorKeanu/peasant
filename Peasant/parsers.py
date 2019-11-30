from http.cookies import SimpleCookie
import re

def parseUrn(s):
    '''Parse the URN value from a string.
    '''

    split = s.split(':')
    identifier = split[-1]
    tag = ':'.join(split[:-1])
    return tag,identifier


def parseCookiesString(cookie_string):
    cookie = SimpleCookie()
    cookie.load(cookie_string)
    return {c:m.value for c,m in cookie.items()}

def parseCompanyId(text_body):
    match = re.search('fs_normalized_company:(?P<cid>.+?)(,.+)?(&quot;])',text_body)
    if not match: return match
    else:
        s = match.groupdict()['cid']
        s = s.replace('&quot;','')
        return s

def parseJSESSIONID(value):

    value = re.search('ajax:([0-9]+)',value) \
            .groups()[0]
    return f'ajax:{value}'

def parseCredentials(credentials):

    # Split the creds on colon
    creds = credentials.split(':')

    # Assure that a username and password is provided
    if creds.__len__() < 2:
        raise Exception('Credentials argument requires a colon ' \
            f'delimited value, not {args.credentials}')

    username = creds[0]

    # Join on colon to assure that colons within the password
    # are captured.
    password = ':'.join(creds[1:])

    return username,password

parseCsrf = parseJSESSIONID

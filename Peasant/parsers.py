from http.cookies import SimpleCookie
import re

def parseCookiesString(cookie_string):
    c = SimpleCookie()
    c.load(cookie_string)
    return {c:m.value for c,m in c.items()}

def parseCompanyId(text_body):
    match = re.search('fs_normalized_company:(?P<cid>.+?)(,.+)?(&quot;])',text_body)
    if not match: return match
    else:
        s = match.groupdict()['cid']
        s = s.replace('&quot;','')
        return s

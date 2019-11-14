import requests
from Peasant.parsers import *

def getInput(prompt):

    i = None
    while not i:
        i = input(prompt)

    return i

def getCredentials():
    
    username = getInput('Username: ')
    password = getInput('Password: ')

    return username,password

def sessionLogin(proxies={},verify_ssl=False):
    '''
    - Get authentication data/cookies resource: /login
    - POST credentials resource: /checkpoint/lg/login-submit

    
    '''
    
    session = requests.Session()
    resp = session.get('https://www.linkedin.com/login',
            proxies=proxies,
            verify=verify_ssl)
    match = re.search(r'name="loginCsrfParam" value="(?P<token>.+?)"',
            resp.text)

    if not match:
        raise Exception('Failed to extract CSRF token from authentication form')

    username = ''
    while not username:
        username = input('Username: ')

    password = ''
    while not password:
        password = getpass()

    resp = session.post(base_url+'/uas/login-submit',
            verify=False,
            headers=headers,
            proxies=proxies,
            data=dict(loginCsrfParam=match.groupdict()['token'],
            session_key=username,session_password=password,
            trk='guest_homepage-basic_sign-in-submit')
        )

    if not resp.url.endswith('basic_sign-in-submit'):
        raise Exception('Authentication failed')

    headers['Accept']='text/event-stream'
    headers['Referer']='https://www.linkedin.com/feed/?trk=guest_' \
            'homepage-basic_sign-in-submit'
    headers['X-RestLi-Protocol-Version']='2.0.0'
    headers['Csrf-Token']=session.cookies.get('JSESSIONID')
    headers['X-LI-Lang']='en_US'
    headers['X-LI-Track']='{"clientVersion":"1.3.4219.0","osName"' \
            ':"web","timezoneOffset":-4,"deviceFormFactor":"DESKT' \
            'OP","mpName":"voyager-web"}'
    headers['X-li-page-instance']='null'
    headers['X-li-accept']='application/vnd.linkedin.normalized+json+2.1'
    session.get(base_url+'/realtime/connect',headers=headers,
            verify=False,proxies=proxies)

    return session

def sessionCookieString(cookies):

    session = requests.Session()
    session.cookies = requests.utils.add_dict_to_cookiejar(
            session.cookies,parseCookiesString(cookies)
        )

    return session

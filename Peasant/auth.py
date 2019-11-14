import requests
from Peasant.parsers import *
from getpass import getpass
import pdb

def getInput(prompt):

    i = None
    while not i:
        i = input(prompt)

    return i

def getCredentials():
    
    username = getInput('Username: ')
    password = getpass('Password: ')

    return username,password

def parseCsrfParam(value):

    return value.split('&')[1][0:-1]

def sessionLogin(username,password,headers={},
        base_url='https://www.linkedin.com',
        proxies={},verify_ssl=False):
    '''

    1. Get cookies required for authentication
    2. Parse cookie data
        - uuid in bcookie value is a CSRF parameter for the POST
          (loginCsrfParam)
        - bcookie="v=2&xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";
    3. POST credentials


    - Get authentication data/cookies resource: /login
    - POST credentials resource: /checkpoint/lg/login-submit
    
    '''
    
    session = requests.Session()

    # Get cookies
    session.get(base_url+'/login',
            headers=headers,
            proxies=proxies,
            verify=verify_ssl)

    # POST credentials
    resp = session.post(base_url+'/checkpoint/lg/login-submit',
                verify=verify_ssl,
                headers=headers,
                proxies=proxies,
                data={
                    'session_key':username,
                    'session_password':password,
                    'loginCsrfParam':parseCsrfParam(
                        session.cookies.get('bcookie')
                    )
                }
            )

    # Determine success
    if resp.status_code != 200 or not resp.request.url.endswith('feed/'):
        raise Exception('Invalid credentials supplied')

    return session

def sessionCookieString(cookies):

    session = requests.Session()
    session.cookies = requests.utils.add_dict_to_cookiejar(
            session.cookies,parseCookiesString(cookies)
        )

    return session

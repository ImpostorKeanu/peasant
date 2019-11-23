import requests
from Peasant.parsers import *
from getpass import getpass
from Peasant.suffix_printer import *
from Peasant.session import *
# from Peasant.generic import *
import pdb

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
    
    session = Session(headers=headers,
            proxies=proxies,
            verify=verify_ssl)

    # Get cookies
    session.get('/login')

    # POST credentials
    resp = session.post('/checkpoint/lg/login-submit',
                data={
                    'session_key':username,
                    'session_password':password,
                    'loginCsrfParam':parseCsrfParam(
                        session.cookies.get('bcookie')
                    )
                }
            )

    try:
        session.headers.update(
            {
                'csrf-token':session.cookies.get('JSESSIONID') \
                        .split('"')[1],
                'x-restli-protocol-version':'2.0.0',
            }
        )
    except:
        raise Exception(
            'Invalid credentials provided. JSESSIONID not found' \
            'in response.')

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

def login(args,headers):

    # Use statically assigned cookies
    if args.cookies:
    
        session = sessionCookieString(args.cookies)
    
    # Get cookies by authentication
    else:
    
        # Handle credentials argument
        if args.credentials:
    
            # Split the creds on colon
            creds = args.credentials.split(':')
    
            # Assure that a username and password is provided
            if creds.__len__() < 2:
                raise Exception('Credentials argument requires a colon ' \
                    f'delimited value, not {args.credentials}')
    
            username = creds[0]
    
            # Join on colon to assure that colons within the password
            # are captured.
            password = ':'.join(creds[1:])
    
        # Get credentials interactively
        else:
    
            esprint('Credentials not provided. Enter credentials to ' \
                    'continue')
            username,password = getCredentials()
    
        # Build the session from the credentials
        return sessionLogin(username,
                password,
                headers=headers,
                proxies=args.proxies,
                verify_ssl=args.verify_ssl,
                base_url=args.url)


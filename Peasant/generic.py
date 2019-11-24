import re
from string import punctuation as PUNCTUATION
from Peasant.profile import *
from Peasant.suffix_printer import *
import csv

def loadProfiles(args):

    main_profiles = []
    with open(args.output_file) as infile:
        rows = [r for r in csv.reader(infile)]
        if rows.__len__() > 2:
            columns = rows[0]
            main_profiles = [
                Profile.from_row(r,columns) for r in rows[1:]
            ]

    return main_profiles

def writeProfiles(args,profiles):

    written=[]
    if args.output_file == stdout:
        csvfile = stdout
    else:
        csvfile = open(args.output_file,'w')
    
    writer = csv.writer(csvfile)
    writer.writerow(Profile.ATTRS)
    for p in profiles:
        if p not in written:
            writer.writerow(p.to_row())
            written.append(p)
    csvfile.close()

def addContacts(session, profiles):
    counter = 0
    for p in profiles:

        # Skip anyprofile without an entity_urn or that has already
        # been requested during a previous run
        if not p.entity_urn or p.connection_requested: continue
        counter += 1
        esprint(f'Sending Connection Request {counter}: {p.first_name} ' \
                f'{p.last_name}, {p.occupation} @ {p.company_name}')
        resp = session.postConnectionRequest(p.entity_urn)
        try:
            status = resp.json()['status']
            if status == 429:
                esprint('API request limit hit. Halting execution')
                break
            else:
                p.connection_requested = True
        except:
            pass

    return profiles

def filterDict(dct,blacklist=[]):
    '''Filter a dictionary based on key values.

    This is useful in situations where we need to adapt the output
    from an API to match the input of a distinct API call when
    spoofing profiles.
    '''

    for key in list(dct.keys()):

        if not key: continue
        
        if key[0] in PUNCTUATION or key in blacklist:
            del(dct[key])
        elif key and dct[key].__class__ == dict:
            dct[key] = filterDict(dct[key])

    return dct


def getInput(prompt,password=False):

    i = None
    while not i:
        if password:
            i = getpass(prompt)
        else:
            i = input(prompt)

    return i

def handleProxies(proxies=[]):

    new_proxies = {}
    if proxies:

        for proxy in proxies:
            match = re.match(r'^(https?)',proxy)
            if not match:
                raise Exception(f'Invalid proxy supplied: {proxy}')
            new_proxies[match.groups()[0]] = proxy
    
    return new_proxies

def getCredentials():
    
    username = getInput('Username: ')
    password = getInput('Password: ',True)

    return username,password

def handleCredentials(args,session):

    # Use statically assigned cookies
    if args.cookies:
    
        session.cookies = requests.utils.add_dict_to_cookiejar(
            session.cookies,parseCookiesString(args.cookies)
        )
    
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

        session.credentialAuth

    return True

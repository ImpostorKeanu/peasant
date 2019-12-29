import re
from string import punctuation as PUNCTUATION
from Peasant.profile import *
from Peasant.suffix_printer import *
from Peasant.parsers import *
from getpass import getpass
import json
import csv
from pathlib import Path
import sqlite3
from sys import exit

def importCookies(filenames):
            
    cookies = {}
    for filename in filenames:

        pth = Path(filename)
        if not pth.exists():
            raise f'File not found: {filename}'

        try:

            with open(filename) as infile:
    
                for jcookie in json.load(infile):
    
                    assert 'name' in jcookie,(
                        'Cookie must have a "name" member'
                    )
    
                    assert 'value' in jcookie,(
                        'Cookie must have a "value" member'
                    )
    
                    cookies[jcookie['name']] = jcookie['value']

        except Exception as e:

            esprint('Failed to import cookies as JSON file. '\
                    'Attempting to parse as SQLite3 file.')

            try:

                with open(filename,'rb') as infile:
                    with open('cookies.sqlite','wb') as outfile:
                        outfile.write(infile.read())
    
                conn = sqlite3.connect('cookies.sqlite')
                cur = conn.cursor()
                for row in cur.execute(
                        f"select * from moz_cookies where "\
                        "baseDomain like '%linkedin%';"
                        ):
                    k,v = row[3],row[4]
                    cookies[k] = v

            except Exception as e:

                esprint('Failed to import cookies!\n\n')
                print(e)
                exit()

    return cookies

def checkEntityUrn(inc,start):
    '''Check if the entityURN member of a JSON object (`inc`)
    starts with with `start`.

    - Returns `True` when a match occurs, otherwise `False`
    '''

    if 'entityUrn' in inc and \
            inc['entityUrn'].startswith(start):
        return True
    else:
        return False

def loadProfiles(output_file):
    '''Load profiles from disk into memory.
    '''

    main_profiles = []
    with open(output_file) as infile:
        rows = [r for r in csv.reader(infile)]
        if rows.__len__() > 2:
            columns = rows[0]
            main_profiles = [
                Profile.from_row(r,columns) for r in rows[1:]
            ]

    return main_profiles

def writeProfiles(output_file,profiles):
    '''Write CSV records to the output file.

    - output_file - str, file-like object - stream which output will 
    be written
    - profiles - list - list of `Peasant.profile.Profile` objects to write
    '''

    written=[]
    if output_file == stdout:
        csvfile = stdout
    else:
        csvfile = open(output_file,'w')
    
    writer = csv.writer(csvfile)
    writer.writerow(Profile.ATTRS)
    for p in profiles:
        if p not in written:
            writer.writerow(p.to_row())
            written.append(p)
    csvfile.close()

def addContacts(session,profiles,message=None):
    '''Use the session object to send connection requests for the
    target profiles.

    - session - `Peasant.session.Session` - Session object used to send
    the requests
    - profiles - list - `list` of `Session.profile.Profile` objects that
    will receive connection requests
    '''

    counter = 0
    for p in profiles:

        # Skip anyprofile without an entity_urn or that has already
        # been requested during a previous run
        if not p.entity_urn or p.connection_requested: continue
        counter += 1
        esprint(f'Sending Connection Request {counter}: {p.first_name} ' \
                f'{p.last_name}, {p.occupation} @ {p.company_name}')

        # Send the connection request
        try:
            resp = session.postConnectionRequest(
                    urn=p.entity_urn,
                    message=message)
        except Exception as e:
            esprint('Failed to send connection request!',suf='[!]')
            raise e

        if resp.status_code == 201:
            p.connection_requested = True
        else:
            try:
                status = resp.json()['status']
                if status == 429:
                    esprint('API request limit hit. Halting execution')
                    break
                else:
                    p.connection_requested = True
            except Exception as e:
                esprint('Connection request failed!',suf='[!]')
                raise e

    return profiles

def filterDict(dct,blacklist=[]):
    '''Filter a dictionary based on key values.

    This is useful in situations where we need to adapt the output
    from an API to match the input of a distinct API call when
    spoofing profiles.

    - dct - `dict` - Dictionary object to filter
    - blacklist - `list` - List of strings which all keys will be
    compared. Matched strings will result in the paired dictionary
    being removed
    '''

    for key in list(dct.keys()):

        if not key: continue
        
        if key[0] in PUNCTUATION or key in blacklist:
            del(dct[key])
        elif key and dct[key].__class__ == dict:
            dct[key] = filterDict(dct[key])

    return dct


def getInput(prompt,password=False):
    '''Get input from the user.

    - prompt - str - Textual prompt that is displayed to user
    - password - bool - Determine if input should be treated as
    a password, resulting in keystrokes being masked
    '''

    i = None
    while not i:
        if password:
            i = getpass(prompt)
        else:
            i = input(prompt)

    return i

def handleProxies(proxies=[]):
    '''Parse each proxy into a dictionary where the key is the protocol
    and the value is the URL to the proxy.

    - proxies - `list` of URLs - A list of URLs to parse as proxies in the
    following format: `https://www.somehost.com:8080`
    '''

    new_proxies = {}
    if proxies:

        for proxy in proxies:
            match = re.match(r'^(https?)',proxy)
            if not match:
                raise Exception(f'Invalid proxy supplied: {proxy}')
            new_proxies[match.groups()[0]] = proxy
    
    return new_proxies

def getCredentials():
    '''Prompt the user to enter credentials interactively.
    '''
    
    username = getInput('Username: ')
    password = getInput('Password: ',True)

    return username,password

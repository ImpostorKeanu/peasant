#!/usr/bin/env python3

import json
import argparse
import warnings
import csv
from sys import stdout
from Peasant.validators import *
from Peasant.parsers import *
from Peasant.generators import *
from Peasant.extractors import *
from Peasant.auth import *
from Peasant.args import parser as arg_parser
warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(
    description='Pull contact invitations from LinkedIn profile.'
)
parser.add_argument('-u','--url',
    default='https://www.linkedin.com',
    help='Base URL to target for requests.')
parser.add_argument('-c','--cookies',
    required=True,
    help='''Cookies needed to access LinkedIn in context of the correct
    user. During development, the following cookies were required: li_at
    and JSESSIONID'
    ''')
parser.add_argument('-of','--output-file',
    default=stdout,
    help='Name of file to receive CSV output.')
parser.add_argument('-p','--proxies',
    nargs='+',
    default=[],
    help='''Space delimited series of upstream proxies that will
    be used to send requests.''',
    required=False)
parser.add_argument('-ua','--user-agent',
    default='Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101' \
        'Firefox/60.0',
    help='User agent string to user.')
parser.add_argument('-vs','--verify-ssl',
    action='store_true',
    help='Verify SSL certificate.')

args = parser.parse_args()

# Prepare request headers
headers = {'User-Agent':args.user_agent}

# Prepare proxies
proxies = {}
for proxy in args.proxies:
    match = re.match(r'^(https?)',proxy)
    if not match:
        raise Exception(f'Invalid proxy supplied: {proxy}')
    proxies[match.groups()[0]] = proxy
args.proxies = proxies

session = sessionCookieString(args.cookies)
session.headers.update(
    {
        'csrf-token':session.cookies.get('JSESSIONID'),
        'x-restli-protocol-version':'2.0.0'
    }
)

print('Getting count of sent invitations: ',end='')
resp = session.get(args.url+'/voyager/api/relationships/' \
        'invitationsSummaryV2?types=List(SENT_INVITATION_COUNT)',
        headers=headers,
        proxies=proxies,
        verify=args.verify_ssl)
total_count = resp.json()['numTotalSentInvitations']
print(total_count)
print('Extracting Invitations')
start=0
pg_size = 300

if total_count > pg_size: count = pg_size
else: count = total_count

print('Collecting invitations and writing them to disk')
with open(args.output_file,'w') as outfile:

    writer = csv.writer(outfile)
    writer.writerow(Profile.ATTRS)

    while True:
    
        resp = session.get(args.url+'/voyager/api/relationships/' \
                'sentInvitationView?q=sent&' \
                f'start={start}&count={count}' \
                '&type=SINGLES_ALL', headers=headers,
                proxies=proxies, verify=args.verify_ssl)

        members=[tm['toMember'] for tm in 
                [hi['heroInvitations'][0] for hi in resp.json()['elements']]
        ]

        for member in members:
            writer.writerow(extractInvitation(member).to_row())

        if start+count == total_count:
            break

        start += count
        if start+pg_size <= total_count: count += pg_size
        else: count = (total_count-start)

print('Finished')

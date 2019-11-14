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
from Peasant.suffix_printer import *
from pathlib import Path
import pdb
warnings.filterwarnings('ignore')

# ==================================
# HANDLE ARGUMENTS AND SET VARIABLES
# ==================================

args = arg_parser.parse_args()

# ========================
# HANDLE PREVIOUS CSV FILE
# ========================

main_profiles = []
if args.output_file != stdout and Path(args.output_file).exists():
    esprint(f'Loading CSV file: {args.output_file}')

    with open(args.output_file) as infile:
        rows = [r for r in csv.reader(infile)]
        if rows.__len__() > 2:
            columns = rows[0]
            main_profiles = [
                Profile.from_row(r,columns) for r in rows[1:]
            ]

    if main_profiles:
        esprint(f'Total profiles loaded: {main_profiles.__len__()}')
    
# == END HANDLING CSV FILE ===

# ==================
# HANDLE CREDENTIALS
# ==================

if args.cookies:
    session = sessionCookieString(args.cookies)
elif args.credentials:
    # TODO: Handle authentication
    pass
else:
    # TODO: Handle interactive authentication
    pass

# == END HANDLE CREDENTIALS ==

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

# ===================================================
# BUILD SESSION OBJECT AND EXTRACT COMPANY IDENTIFIER
# ===================================================

# Build a session using the supplied cookies
session = sessionCookieString(args.cookies)
for company_name in args.company_names:
    
    # Make the initial response to obtain the company identifier
    resp = session.get(args.url+'/company/'+company_name+'/people/',
            headers=headers,
            proxies=args.proxies,
            verify=args.verify_ssl)
    cid = company_id = parseCompanyId(resp.text)
    esprint(f'Company Identifier for {company_name}: {cid}')
    
    # Update headers with CSRF token and restli header
    jsessionid = session.cookies.get('JSESSIONID')

    if not jsessionid:

        raise Exception(
                'JSESSIONID not found in response. This is indicative ' \
                'of invalid cookie values being supplied.'
            )

    session.headers.update(
        {
            'csrf-token':jsessionid,
            'x-restli-protocol-version':'2.0.0'
        }
    )
    
    # =========================
    # BEGIN EXTRACTING PROFILES
    # =========================
    
    # Get the initial set of profiles to determine the total available
    # number.
    esprint('Getting initial profiles')
    resp = session.get(genVoyagerSearchURL(args.url,cid,0,10),
        headers=headers,proxies=args.proxies,verify=args.verify_ssl)
    
    # Parse the response and extract the information into profiles
    j = resp.json()
    count,profiles = extractInfo(j,company_name,cid)
    esprint(f'Available profiles: {count}')
    
    # ==========================
    # EXTRACT REMAINING PROFILES
    # ==========================
    
    esprint('Extracting remaining profiles...')
    offset = 10
    mfv = max_facet_values = 10
    while True:
        resp = session.get(genVoyagerSearchURL(args.url,cid,offset,mfv),
                headers=headers,proxies=args.proxies,
                verify=args.verify_ssl)
        icount,iprofiles = extractInfo(resp.json(),company_name,cid)
        profiles += iprofiles
        if offset >= count or offset >= 999: break
        offset += mfv
        if offset >= 1000: offset = 999

    # =========================
    # CAPTURE ONLY NEW PROFILES
    # =========================

    for profile in profiles:
        if profile not in main_profiles:
            main_profiles.append(profile)

esprint(f'Done! Total known profiles: {main_profiles.__len__()}')

# ============
# ADD CONTACTS
# ============

if args.add_contacts:
    add_url = args.url+'/voyager/api/growth/normInvitations'
    esprint(f'Sending connection requests...')
    counter = 0
    for p in main_profiles:
        if not p.entity_urn or p.connection_requested: continue
        counter += 1
        p.connection_requested = True
        esprint(f'Sending Connection Request {counter}: {p.first_name} {p.last_name}, ' \
              f'{p.occupation} @ {p.company_name}')
        data = {"emberEntityName":"growth/invitation/norm-invitation",
                "invitee":{
                    "com.linkedin.voyager.growth.invitation.InviteeProfile":{
                        "profileId":f"{p.entity_urn}"
                        }
                    },
                "trackingId":"86us0JMVTy6fXUztPyFKhw=="}
        session.post(add_url,headers=headers,proxies=args.proxies,
                verify=args.verify_ssl,json=data)
# ===========
# DUMP OUTPUT
# ===========

esprint(f'Writing output to {args.output_file}')

csv_headers = Profile.ATTRS
written=[]
if args.output_file == stdout:
    csvfile = stdout
else:
    csvfile = open(args.output_file,'w')

writer = csv.writer(csvfile)
writer.writerow(csv_headers)
for p in main_profiles:
    if p not in written:
        writer.writerow(p.to_row())
        written.append(p)

esprint('Done!')
csvfile.close()

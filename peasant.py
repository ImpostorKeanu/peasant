#!/usr/bin/env python3

import json
import argparse
import warnings
import csv
from Peasant.validators import *
from Peasant.parsers import *
from Peasant.generators import *
from Peasant.extractors import *
from Peasant.auth import *
from Peasant.args import parser as arg_parser
warnings.filterwarnings('ignore')

# ==================================
# HANDLE ARGUMENTS AND SET VARIABLES
# ==================================

args = arg_parser.parse_args()

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
main_profiles = []
for company_name in args.company_names:
    
    # Make the initial response to obtain the company identifier
    resp = session.get(args.url+'/company/'+company_name+'/people/',
            headers=headers,
            proxies=args.proxies,
            verify=args.verify_ssl)
    cid = company_id = parseCompanyId(resp.text)
    print(f'Company Identifier for {company_name}: {cid}')
    
    # Update headers with CSRF token and restli header
    session.headers.update(
        {
            'csrf-token':session.cookies.get('JSESSIONID'),
            'x-restli-protocol-version':'2.0.0'
        }
    )
    
    # =========================
    # BEGIN EXTRACTING PROFILES
    # =========================
    
    # Get the initial set of profiles to determine the total available
    # number.
    print('Getting initial profiles')
    resp = session.get(genVoyagerSearchURL(args.url,cid,0,10),
        headers=headers,proxies=args.proxies,verify=args.verify_ssl)
    
    # Parse the response and extract the information into profiles
    j = resp.json()
    count,profiles = extractInfo(j)
    print(f'Available profiles: {count}')
    
    # ==========================
    # EXTRACT REMAINING PROFILES
    # ==========================
    
    print('Extracting remaining profiles...')
    offset = 10
    mfv = max_facet_values = 10
    while True:
        resp = session.get(genVoyagerSearchURL(args.url,cid,offset,mfv),
                headers=headers,proxies=args.proxies,
                verify=args.verify_ssl)
        icount,iprofiles = extractInfo(resp.json())
        profiles += iprofiles
        if offset >= count or offset >= 999: break
        offset += mfv
        if offset >= 1000: offset = 999

    main_profiles += profiles

# ===========
# DUMP OUTPUT
# ===========

print(f'Writing output to {args.output_file}')

csv_headers = Profile.ATTRS
written=[]
with open(args.output_file, 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(csv_headers)
    for p in main_profiles:
        if p not in written:
            writer.writerow(p.to_row())
            written.append(p)

# ============
# ADD CONTACTS
# ============

if args.add_contacts:
    add_url = args.url+'/voyager/api/growth/normInvitations'
    print(f'Attempting to add contacts')
    for p in main_profiles:
        if not p.entity_urn: continue
        print(f'Adding profile urn: {p.entity_urn}')
        data = {"emberEntityName":"growth/invitation/norm-invitation",
                "invitee":{
                    "com.linkedin.voyager.growth.invitation.InviteeProfile":{
                        "profileId":f"{p.entity_urn}"
                        }
                    },
                "trackingId":"86us0JMVTy6fXUztPyFKhw=="}
        session.post(add_url,headers=headers,proxies=args.proxies,
                verify=args.verify_ssl,json=data)

print('Done!')

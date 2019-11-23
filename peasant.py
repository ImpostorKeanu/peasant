#!/usr/bin/env python3

import json
import argparse
import warnings
import csv
from sys import stdout, exit
from pathlib import Path
from Peasant.validators import *
from Peasant.parsers import *
from Peasant.generators import *
from Peasant.extractors import *
from Peasant.auth import *
from Peasant.args import parser as arg_parser
from Peasant.suffix_printer import *
from Peasant.banner import banner
from Peasant.generic import *
import pdb

warnings.filterwarnings('ignore')

print(banner)

# ==================================
# HANDLE ARGUMENTS AND SET VARIABLES
# ==================================

args = arg_parser.parse_args()
headers = {'User-Agent':args.user_agent}

# ===========
# SET PROXIES
# ===========

args.proxies = handleProxies(args.proxies)

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
    
# ==================
# HANDLE CREDENTIALS
# ==================

session = Session(headers=headers,
        proxies=args.proxies,
        verify=args.verify_ssl)
basic_profile = session.login(args)
session.spoofProfile('erika-mcduffie-767394bb')
exit()

# ============================
# BEGIN EXTRACTING INFORMATION
# ============================

for company_name in args.company_names:

    # ===================================================
    # BUILD SESSION OBJECT AND EXTRACT COMPANY IDENTIFIER
    # ===================================================
    
    # Make the initial response to obtain the company identifier
    cid = company_id = session.getCompanyId(company_name)
    esprint(f'Company Identifier for {company_name}: {cid}')

    # =========================
    # BEGIN EXTRACTING PROFILES
    # =========================
    
    # Get the initial set of profiles to determine the total available
    # number.
    esprint('Getting initial profiles')
    #resp = session.get(genVoyagerSearchPath(cid,0,10))
    resp = session.getContactSearchResults(cid,0,10)
    
    # Parse the response and extract the information into profiles
    count,profiles = extractInfo(resp.json(),company_name,cid)
    esprint(f'Available profiles: {count}')
    
    # ==========================
    # EXTRACT REMAINING PROFILES
    # ==========================
    
    esprint('Extracting remaining profiles (this will take some time)')
    offset = 10
    mfv = max_facet_values = 10
    while True:
        resp = session.getContactSearchResults(cid,offset,mfv)
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

    esprint(f'Sending connection requests...')
    counter = 0
    for p in main_profiles:

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

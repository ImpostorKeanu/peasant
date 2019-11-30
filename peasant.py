#!/usr/bin/env python3

import json
import argparse
import warnings
import csv
from sys import stdout, exit
from pathlib import Path
from Peasant.parsers import *
from Peasant.generators import *
from Peasant.extractors import *
from Peasant.session import Session
from Peasant.args import parser as arg_parser
from Peasant.suffix_printer import *
from Peasant.banner import banner
from Peasant.generic import *
from Peasant.exceptions import *
from Peasant.constants import *
from Peasant.harvest import harvest_contacts

warnings.filterwarnings('ignore')

print(banner)

# ==================================
# HANDLE ARGUMENTS AND SET VARIABLES
# ==================================

args = arg_parser.parse_args()
if not args.cmd:
    arg_parser.print_help()
    exit()
headers = {'User-Agent':args.user_agent}

# ===========
# SET PROXIES
# ===========

args.proxies = handleProxies(args.proxies)

# ========================
# HANDLE PREVIOUS CSV FILE
# ========================

if 'output_file' in args.__dict__:

    if args.output_file != stdout and Path(args.output_file).exists():
        esprint(f'Loading CSV file: {args.output_file}')
        main_profiles = loadProfiles(args.output_file)
        esprint(f'Total profiles loaded: {main_profiles.__len__()}')
    else:
        if args.output_file != stdout:
            esprint(f'Starting new CSV file: {args.output_file}')
        main_profiles = []

try:

    # =====================
    # HANDLE AUTHENTICATION
    # =====================
    
    session = Session(headers=headers,
            proxies=args.proxies,
            verify=args.verify_ssl)
    
    esprint('Authenticating session')
    session.login(args)
    profile = session.getBasicProfile()

    if not session.authenticated:
        esprint('Authentication failed! Check credential settings ' \
                'and try again.')
        exit()
    
    if profile.premiumSubscriber:
        esprint('Authenticated as a premium subscriber')
    
    # ===============
    # EXECUTE COMMAND
    # ===============
    
    # Harvest contacts
    if args.cmd == 'harvest_contacts':
    
        harvest_contacts(args,session,main_profiles)
    
    # Add contacts from CSV file
    elif args.cmd == 'add_contacts':
       
        esprint('Sending connection requests, which will take '\
                'some time...')
        main_profiles = addContacts(session,main_profiles,args.message)
        esprint(f'Writing profiles to file: {args.output_file}')
        writeProfiles(args.output_file,main_profiles)
    
    # Profile spoofing
    elif args.cmd == 'spoof_contact':
       
        esprint('Spoofing basic profile information...')
        session.spoofBasicInfo(args.public_identifier)
    
        esprint('Clearing current profile education and spoofing ' \
                'target content...')
        session.deleteEducation()
        session.spoofEducation(args.public_identifier)
    
        esprint('Clearing current profile experience and spoofing ' \
                'target content...')
        session.deleteExperience()
        session.spoofExperience(args.public_identifier)

        esprint('Spoofing profile images...')
        session.spoofPictures(args.public_identifier)

        esprint('Spoofing complete!')

finally:

    esprint('Logging out')
    session.getLogout()
    esprint('Done...exiting')

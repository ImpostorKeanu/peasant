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
from Peasant.exceptions import *
from Peasant.harvest import harvest_contacts
import pdb

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
        main_profiles = loadProfiles(args)
        esprint(f'Total profiles loaded: {main_profiles.__len__()}')
    else:
        esprint(f'Starting new CSV file: {args.output_file}')
        main_profiles = []
    
# ==================
# HANDLE CREDENTIALS
# ==================
session = Session(headers=headers,
        proxies=args.proxies,
        verify=args.verify_ssl)
session.login(args)

if not session.authenticated:
    esprint('Authentication failed! Check credential settings and ' \
            'try again.')
    exit()

if args.cmd == 'harvest':
    harvest_contacts(args,session)
elif args.cmd == 'add_contacts':
    pass
elif args.cmd == 'spoof_profile':
   
    esprint('Spoofing basic profileinformation...',end='')
    session.spoofBasicInfo(args.public_identifier)
    print('done',file=stdout)

    esprint('Clearing current profile education and spoofing ' \
            'target content...',end='')
    session.deleteEducation()
    session.spoofEducation(args.public_identifier)
    print('done',file=stdout)

    esprint('Clearing current profile experience and spoofing ' \
            'target content...',end='')
    session.deleteExperience()
    session.spoofExperience(args.public_identifier)
    print('done',file=stdout)

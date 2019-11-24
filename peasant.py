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

pargs = arg_parser.parse_args()
exit()

headers = {'User-Agent':args.user_agent}

# ===========
# SET PROXIES
# ===========

args.proxies = handleProxies(args.proxies)

# ========================
# HANDLE PREVIOUS CSV FILE
# ========================

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

#if args.command == 'harvest':
#    harvest_contacts(args,session)

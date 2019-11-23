import argparse
from sys import stdout
from Peasant.banner import banner

parser = argparse.ArgumentParser(
    description=f'''Detect, generate, and collect connection requests
    from LinkedIn'''
)

# ===================
# OPERATIONAL OPTIONS
# ===================

operational_group = parser.add_argument_group('Operational Parameters (REQUIRED)',
        description='''Determine the companies to target and
        if connection requests should be generated.''')
operational_group.add_argument('-cns','--company-names',
    nargs='+',
    required=True,
    help='''Space delimited LinkedIn company names as observed in
    URL of company profile, e.g.: the identifier in the following URL
    would be 'black-hills-information-security:
    /company/black-hills-information-security/people/
    ''')
operational_group.add_argument('-ac','--add-contacts',
    action='store_true',
    help='''When possible, attempt to make a connection request
    for a contact. Default: %(default)s
    ''')

# ======================
# AUTHENTICATION OPTIONS
# ======================

auth_options = parser.add_argument_group('Authentication Parameters (OPTIONAL)',
        description='''Determine how to authenticate to LinkedIn. User is
        prompted for credentials if one of these mutually-exclusive options
        are not provided.
        ''')
credential_group = auth_options.add_mutually_exclusive_group()
credential_group.add_argument('-C','--credentials',
    help='''Colon delimited credentials, e.g. 'username:password', to
    use for authentication.
    ''')
credential_group.add_argument('-c','--cookies',
    help='''Cookies needed to access LinkedIn in context of the correct
    user. During development, the following cookies were required: li_at
    and JSESSIONID'
    ''')

# ==============
# OUTPUT OPTIONS
# ==============

output_group = parser.add_argument_group('Output Parameters (OPTIONAL)',
        description='Configure output options.')
output_group.add_argument('-of','--output-file',
    default=stdout,
    help='''Name of file to receive CSV output (Default: stdout). If a
    file name is provided and that file already exists, it will be read
    into memory and be treated as previous output. This provides a level
    of efficiency by allowing the scrept to avoid sending multiple connection
    requests for the same profile.
    ''')

# ============
# MISC OPTIONS
# ============

misc_group = parser.add_argument_group('Miscellaneous Parameters (OPTIONAL)',
        description='Additional parameters with sane defaults')
misc_group.add_argument('-u','--url',
    default='https://www.linkedin.com',
    help='Base URL to target for requests. Default: %(default)s')
misc_group.add_argument('-p','--proxies',
    nargs='+',
    default=[],
    help='''Space delimited series of upstream proxies that will
    be used to send requests.''',
    required=False)
misc_group.add_argument('-ua','--user-agent',
    default='Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101' \
        'Firefox/60.0',
    help='User agent string. Default: %(default)s')
misc_group.add_argument('-vs','--verify-ssl',
    action='store_true',
    help='Verify SSL certificate. Default: %(default)s')

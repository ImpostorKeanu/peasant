import argparse
from sys import stdout
from Peasant.banner import banner

class Argument:

    def __init__(self,*args,**kwargs):

        self.args = args
        self.kwargs = kwargs

    def add(self,target):

        target.add_argument(*self.args,**self.kwargs)

# == DEFINE REUSABLE ARGUMENTS

# ===================
# OPERATIONAL OPTIONS
# ===================

company_names = Argument('-cns','--company-names',
    nargs='+',
    required=True,
    help='''Space delimited LinkedIn company names as observed in
    URL of company profile, e.g.: the identifier in the following URL
    would be 'black-hills-information-security:
    /company/black-hills-information-security/people/
    ''')
add_contacts = Argument('-ac','--add-contacts',
    action='store_true',
    help='''When possible, attempt to make a connection request
    for a contact. Default: %(default)s
    ''')

# ======================
# AUTHENTICATION OPTIONS
# ======================

credentials = Argument('-C','--credentials',
    help='''Colon delimited credentials, e.g. 'username:password', to
    use for authentication.
    ''')
cookies = Argument('-c','--cookies',
    nargs='+',
    help='''One or more JSON files containing cookies to support
    authentication to LinkedIn. Each file should contain an array
    of JSON objects with a name member containing the name of the
    current cookie and a value member containing the value of the
    current cookie, i.e.
    [{"name":"cookie_name","value":"cookie_value"}]. I elected to
    make this change from a string of cookies because there is a
    chance that additional cookies may be introduced in the future
    and this approach is more easily managed. Use a browser extension
    like CookieBro to export these values from FireFox.
    ''')

# ==============
# OUTPUT OPTIONS
# ==============

output_file = Argument('-of','--output-file',
    default=stdout,
    help='''Name of file to receive CSV output (Default: stdout). If a
    file name is provided and that file already exists, it will be read
    into memory and be treated as previous output. This provides a level
    of efficiency by allowing the script to avoid sending multiple connection
    requests for the same profile.
    ''')

# ============
# MISC OPTIONS
# ============

url = Argument('-u','--url',
    default='https://www.linkedin.com',
    help='Base URL to target for requests. Default: %(default)s')
proxies = Argument('-p','--proxies',
    nargs='+',
    default=[],
    help='''Space delimited series of upstream proxies that will
    be used to send requests.''',
    required=False)
user_agent = Argument('-ua','--user-agent',
    default='Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101' \
        ' Firefox/60.0',
    help='User agent string. Default: %(default)s')
verify_ssl = Argument('-vs','--verify-ssl',
    action='store_true',
    help='Verify SSL certificate. Default: %(default)s')
disable_logout = Argument('--disable-logout',
    action='store_true',
    help='''Preserve cookies for additional requests by disabling the
    logout call after execution. Default: %(default)s''')

# =============
# OTHER OPTIONS
# =============

public_identifier = Argument('-pu','--public-identifier',
        help='Public identifier of target profile',
        required=True)
input_file = Argument('-if','--input-file',
        help='Input CSV file to extract records',
        required=True,
        dest='output_file')

# == END ARGUMENT DEFINITION ==

# =============================
# ARGUMENT PARSER CONFIGURATION
# =============================

parser = argparse.ArgumentParser(
    description=f'''Use the LinkedIn API to collect user information,
    spoof profile content, and generate connection requests.'''
)
parser.set_defaults(cmd=None)
subparsers = parser.add_subparsers(help='Supported Subcommands',
        metavar='')

# =================
# HARVEST SUBPARSER
# =================

harvest = subparsers.add_parser('harvest_contacts',
        aliases=['harvest','h'],
        help='''Harvest contacts from LinkedIn while allowing
        for automated connection request generation.
        ''')
harvest.set_defaults(cmd='harvest_contacts')

# Operational options
operational_group = harvest.add_argument_group('Operational Parameters (REQUIRED)',
        description='''Determine the companies to target and
        if connection requests should be generated.''')
company_names.add(operational_group)
add_contacts.add(operational_group)

# Output Options
output_group = harvest.add_argument_group('Output Parameters (OPTIONAL)',
        description='Configure output options.')
output_file.add(output_group)

# Auth Options
auth_options = harvest.add_argument_group('Authentication Parameters (OPTIONAL)',
        description='''Determine how to authenticate to LinkedIn. User is
        prompted for credentials if one of these mutually-exclusive options
        are not provided.
        ''')
credential_group = auth_options.add_mutually_exclusive_group()
credentials.add(credential_group)
cookies.add(credential_group)

# MISC Options
misc_group = harvest.add_argument_group('Miscellaneous Parameters (OPTIONAL)',
        description='Additional parameters with sane defaults')
url.add(misc_group)
proxies.add(misc_group)
user_agent.add(misc_group)
verify_ssl.add(misc_group)
disable_logout.add(misc_group)


# ======================
# ADD CONTACTS SUBPARSER
# ======================

add_contacts = subparsers.add_parser('add_contacts',
    aliases=['add','a'],
    help='''Create LinkedIn connection requests from a CSV file
    generated by Peasant.
    ''')
add_contacts.set_defaults(cmd='add_contacts')

input_options = add_contacts.add_argument_group(
        'Input Options (REQUIRED)'
    )
input_file.add(input_options)
input_options.add_argument('-m','--message',
    default=None,
    help='''Message to send for each connection request. (OPTIONAL)
    ''')

# Auth Options
auth_options = add_contacts.add_argument_group('Authentication Parameters (OPTIONAL)',
        description='''Determine how to authenticate to LinkedIn. User is
        prompted for credentials if one of these mutually-exclusive options
        are not provided.
        ''')
credential_group = auth_options.add_mutually_exclusive_group()
credentials.add(credential_group)
cookies.add(credential_group)

# MISC Options
misc_group = add_contacts.add_argument_group('Miscellaneous Parameters (OPTIONAL)',
        description='Additional parameters with sane defaults')
url.add(misc_group)
proxies.add(misc_group)
user_agent.add(misc_group)
verify_ssl.add(misc_group)
disable_logout.add(misc_group)

# ===============
# SPOOF SUBPARSER
# ===============

spoof = subparsers.add_parser('spoof_contact',
        aliases=['spoof','s'],
        help='''Spoof basic profile information, education,
        and experience from a LinkedIn profile to your profile
        ''')
spoof.set_defaults(cmd='spoof_contact')

# Targeting Options
targeting_options = spoof.add_argument_group(
        'Targeting Options (REQUIRED)')
public_identifier.add(targeting_options)

# Auth Options
auth_options = spoof.add_argument_group('Authentication Parameters (OPTIONAL)',
        description='''Determine how to authenticate to LinkedIn. User is
        prompted for credentials if one of these mutually-exclusive options
        are not provided.
        ''')
credential_group = auth_options.add_mutually_exclusive_group()
credentials.add(credential_group)
cookies.add(credential_group)

# MISC Options
misc_group = spoof.add_argument_group('Miscellaneous Parameters (OPTIONAL)',
        description='Additional parameters with sane defaults')
url.add(misc_group)
proxies.add(misc_group)
user_agent.add(misc_group)
verify_ssl.add(misc_group)
disable_logout.add(misc_group)


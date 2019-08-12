import argparse

parser = argparse.ArgumentParser(
    description='Pull contacts from an authenticated LinkedIn session.'
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
parser.add_argument('-cns','--company-names',
    nargs='+',
    required=True,
    help='''Space delimited LinkedIn company names, as observed in URL of company profile,
    e.g.: BHIS identifier in /company/black-hills-information-security/people/
    ''')
parser.add_argument('-of','--output-file',
    required=True,
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
parser.add_argument('-ac','--add-contacts',
    action='store_true',
    help='When possible, attempt to add contact.')

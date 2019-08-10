# Peasant: Extract Profile Information from an Authenticated LinkedIn Session

_Before running this_ you'll likely want maximize the number of accessible accounts by getting a few connections with the target company.

The LinkedIn web interface pulls accounts from an API when browsing the `/people` path of a company profile. Output from each call is highly structured, minimizing guess work involved with extracting fields from each profile. `Peasant` automates the process of extracting profiles for a given company by crafting the API calls and dumping the output to a CSV file.

# Usage

## Handling Cookies

The developer elected not to implement authentication in this utility to minimize maintenance of this tool, i.e. it's unknown how often LinkedIn changes the authentication process and he's too lazy to keep an eye on it (spoilers: it's more complex than just authenticating and pulling records). This means cookies must be supplied at the command line in order to access LinkedIn in context of the desired user.

It seems like a pain, but only the following cookies appear to be required as of August 2019: `JSESSIONID`, `li_at`. I find it fairly easy to set the cookie header as an environment variable and passing it to the command.

The easiest way to get these values is to use the developer tools and access the storage tab, allowing textual access directly to the cookies.

## Example

Here is a basic example command:

```
export cookies='JSESSIOND=<theidentifier>;li_at=<thevalue>;'
./peasant.py --cookies "$cookies" \
    -of linked_test.csv \
    -cn black-hills-information-security \
    --proxies https://192.168.1.246:8081
```

Here is output from the command above:

```
Company Identifier for black-hills-information-security: 3569774
Getting initial profiles
Available profiles: 47
Extracting remaining profiles
10 extractions...
20 extractions...
30 extractions...
40 extractions...
50 extractions...
Writing output to linked_test.csv
Done!
```

# Peasant

Peasant is a LinkedIn reconnaissance utility that functions much like
[LinkedInt](https://github.com/vysecurity/LinkedInt). It authenticates
to LinkedIn and uses the API to perform several tasks, each of which
are outline below.

## Contact Harvesting

By supplying one or more company names to the `harvest` command,
Peasant will make API calls to acquire the numeric identifier of
the company and proceed to enumerate employees from the people
section of the target profile.

If the target is Dunder Mifflin Design and the company name was found
to be `dundermifflindesign` via search engine, then the following command
would attempt to harvest profiles and write CSV records to dundermifflin.csv:

_WARNING_: Use of the `-ac` flag will result in a connection request being
sent to each accessible profile. If you wish to filter for particlar profiles,
use the `-of` flag to dump the results to disk and select specific records
via grep and use the `add_contacts` subcommand to create connection requests.

```bash
archangel@deskjet~~> export creds='username_here:password_here' # or 
interactive authentication 
archangel@deskjet~~> ./peasant.py harvest -C "$creds" -cns 
dundermifflindesign -of dundermifflin.csv

    //   ) )
   //___/ /  ___      ___      ___      ___       __    __  ___
  / ____ / //___) ) //   ) ) ((   ) ) //   ) ) //   ) )  / /
 //       //       //   / /   \ \    //   / / //   / /  / /
//       ((____   ((___( ( //   ) ) ((___( ( //   / /  / /

[+] Starting new CSV file: dundermifflin.csv
[+] Authenticating session
[+] Authenticated as a premium subscriber
[+] Company Identifier for dundermifflindesign: 19067092
[+] Getting initial profiles
[+] Available profiles: 101
[+] Logging out of LinkedIn
[+] Writing output to dundermifflin.csv
[+] Done!
[+] Logging out
[+] Done...exiting
```

### Limitations

LinkedIn will allow only the first 1,000 search results to be returned
when harvesting contact information, however the same results are not
returned each time a series of searches are applied. Run the harvest
command multiple times to capture more contacts.

Here are two ways to increase the number of contacts a given profile
can access:

1. Generate connection requests for company people via the `add_contacts`
subcommand or the `-ac` flag of the `harvest` command
2. Update the target profile such that you are in a position at the target
company. This appears to facilitate access to more contacts initially.

## Connection Request Generation

Use the `add_contacts` subcommand to generate connection requests for
target profiles. This command takes the name of a CSV file generated
by the `harvest` subommand and will indiscriminately send a connection
request for each record.

## Profile Spoofing

# Subcommands

from Peasant.exceptions import *
from Peasant.suffix_printer import *
from Peasant.extractors import *
from Peasant.generic import *

def harvest_contacts(args,session):

    # ============================
    # BEGIN EXTRACTING INFORMATION
    # ============================
    
    for company_name in args.company_names:
    
        # ===================================================
        # BUILD SESSION OBJECT AND EXTRACT COMPANY IDENTIFIER
        # ===================================================
        
        # Make the initial response to obtain the company identifier
        try:
            cid = company_id = session.getCompanyId(company_name)
            esprint(f'Company Identifier for {company_name}: {cid}')
        except SessionException:
            esprint(f'Failed to get company identifier for {company_name} ' \
                    'Continuing to next company')
    
        # =========================
        # BEGIN EXTRACTING PROFILES
        # =========================
        
        # Get the initial set of profiles to determine the total available
        # number.
        esprint('Getting initial profiles')
        resp = session.getContactSearchResults(cid,0,10)
        
        # Parse the response and extract the information into profiles
        count,profiles = extractInfo(resp.json(),company_name,cid)
        esprint(f'Available profiles: {count}')
        
        # ==========================
        # EXTRACT REMAINING PROFILES
        # ==========================
        
        esprint('Extracting remaining profiles (this will take some time)')
        offset,max_facet_values = 10,10
        profiles = extractProfiles(session,offset=offset,
                max_facet_values=max_facet_values)
    
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
        main_profiles = addContacts(session,main_profiles)
    
    # ===========
    # DUMP OUTPUT
    # ===========
    
    esprint(f'Writing output to {args.output_file}')
    writeProfiles(args,main_profiles)
    esprint('Done!')

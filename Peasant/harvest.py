from Peasant.exceptions import *
from Peasant.suffix_printer import *
from Peasant.extractors import *
from Peasant.generic import *

class Company:

    def __init__(self,session,company_name,step_size=10):

        self.harvested=False

        # track the company_name
        self.company_name=company_name

        # maintain step size for each profile request
        self.step_size=step_size

        # maintain previous offset call for next call
        self.last_offset=-1
        self.offset=0
        self.next_offset=step_size

        # keep track of profiles for each company name
        self.profiles=[]

        self.company_id = None
        self.profile_count = None

        # ========================================
        # GET THE company_id FROM THE company_name
        # ========================================

        try:
            self.company_id = session.getCompanyId(self.company_name)
            esprint(f'Company Identifier for {company_name}: {cid}')
        except SessionException:
            esprint(f'Failed to get company identifier for {self.company_name} ' \
                    'Continuing to next company')

        # ========================
        # EXTRACT INITIAL PROFILES
        # ========================

        esprint('Getting initial profiles')

        # Get profiles
        resp = session.getContactSearchResults(self.company_id,0,self.step_size)

        # Extract info from the profiles
        self.profile_count, profiles = extractInfo(resp.json(),company_name,cid)
        self.profiles += profiles

        esprint(f'Available profiles: {count}')
        self.step()

    def step(self):

        self.last_offset=self.offset
        self.offset=self.next_offset
        self.next_offset+=self.step_size

        if self.next_offset > self.profile_count:
            self.next_offset=self.profile_count
        elif self.next_offset >= 1000:
            self.next_offset = 999

        return self.offset

    def is_finished(self):

        if self.harvested:
            return True

        elif [n for n in [self.offset,self.last_offset] if n >= 999] or \
                self.profiles.__len__() >= self.profile_count:
            self.harvested=True
            return True

        else:
            return False

def harvest_contacts(args,session,main_profiles=[]):

    # ============================
    # BEGIN EXTRACTING INFORMATION
    # ============================

    # Get initial profiles for each company_name value
    # Initialize a member of the OFFSETS variable for that company_name
    #    - OFFSETS["company_name"]=(last_min,last_max)
   
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
        # TODO: Adjust offsets to make this more efficient
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
        profiles = extractProfiles(session=session,
                company_name=company_name,
                company_id=cid,
                offset=offset,
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

        # Must track profiles here since addContacts will
        # update the connection_sent attribute to True
        main_profiles = addContacts(session,main_profiles)
    
    # ===========
    # DUMP OUTPUT
    # ===========
    
    esprint(f'Writing output to {args.output_file}')
    writeProfiles(args.output_file,main_profiles)
    esprint('Done!')

def fuzzy_harvest_contacts(args,session,main_profiles=[]):

    # ============================
    # BEGIN EXTRACTING INFORMATION
    # ============================
  
    companies = []
    for company_name in args.company_names:

        companies.append(Company(session,company_name))

    fuzzyExtractProfiles(session,companies,max_jitter='10s')

    for company in companies:
    
        # =========================
        # CAPTURE ONLY NEW PROFILES
        # =========================
    
        for profile in company.profiles:
            if profile not in main_profiles:
                main_profiles.append(profile)
    
    esprint(f'Done! Total known profiles: {main_profiles.__len__()}')
    
    # ============
    # ADD CONTACTS
    # ============
    
    if args.add_contacts:
    
        esprint(f'Sending connection requests...')

        # Must track profiles here since addContacts will
        # update the connection_sent attribute to True
        main_profiles = addContacts(session,main_profiles)
    
    # ===========
    # DUMP OUTPUT
    # ===========
    
    esprint(f'Writing output to {args.output_file}')
    writeProfiles(args.output_file,main_profiles)
    esprint('Done!')

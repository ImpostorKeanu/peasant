from Peasant.profile import Profile
from Peasant.picture import Picture
from Peasant.image import Image
from re import sub
import pdb

def extractImages(root_url,artifacts,session):
    '''Extract picture linke from a JSON object.
    '''

    # TODO: The following logic recklessly assumes
    # that the picture JSON object will include an
    # array of objects that are _ordered by size_
    # from smallest to largest. Review this logic
    # and develop a way to detect the size based on
    # width and height.

    picture,size = {},'small'
    for artifact in artifacts:

        # Construct the URI for the target image
        url = \
                root_url + \
                artifact['fileIdentifyingUrlPathSegment']

        # Initialize an Image object and load the
        # binary content
        picture[size] = Image(size,url)
        picture[size].load(session)

        # Break if we've met extra large size
        if size == 'xlarge': break

        # Get the next size
        size = {'small':'medium',
                'medium':'large',
                'large':'xlarge'}[size]

    # initialize and return a picture object
    return Picture(**picture)

def extractInfo(j,company_name,company_id):
    '''Extract information from the JSON object returned after
    making an API call to LinkedIn. Returns an integer indicating
    the total number of results and a list of Peasant.profile objects,
    each representing an individual profile.
    '''

    '''Path to total result count:
       - /metadata/totalResultCount

    Path to element objects:
    - /elements
    '''

    result_count = j['metadata']['totalResultCount']
    to_parse = []
    for e in j['elements']:

        if 'hitInfo' in e and 'com.linkedin.voyager.search.SearchProfile' in \
                e['hitInfo']:
                    to_parse.append(e)

    return result_count,[extractProfile(e,company_name,company_id) for e in to_parse]

def extractProfile(jelement,company_name,company_id):
    '''Derive and return Peasant.profile object from an element.
    '''

    j = jelement

    '''Path to profile information from element:
    - /hitInfo/com.linkedin.voyager.search.SearchProfile
    '''

    profile = j['hitInfo']['com.linkedin.voyager.search.SearchProfile']

    # get industry/location information
    industry = profile.get('industry')
    location = profile.get('location')

    # get profile information

    mini_profile = profile['miniProfile']
    first_name = mini_profile['firstName']
    last_name = mini_profile['lastName']
    occupation = mini_profile['occupation']
    public_identifier = mini_profile['publicIdentifier']
    entity_urn = mini_profile['entityUrn']
    if entity_urn:
        try:
            entity_urn = entity_urn.split(':')[-1]
        except:
            entity_urn = None

    # return a Peasant.profile object
    return Profile(first_name,last_name,occupation,
            public_identifier,industry,location,entity_urn,company_name,company_id)

def extractInvitation(jelement):
    '''Derive and return a Peasant.profile object from a JSON object
    ("toMember).
    '''

    j = jelement
    return Profile(first_name=j['firstName'],last_name=j['lastName'],
            occupation=j['occupation'],
            entity_urn=j['entityUrn'].split(':')[-1],
            public_identifier=j['publicIdentifier'])

def extractProfiles(session,company_name,company_id,offset=10,
        max_facet_values=10):

    profiles = []
    while True:

        resp = session.getContactSearchResults(company_id,
                offset,max_facet_values)

        icount,iprofiles = extractInfo(resp.json(),
                company_name,company_id)

        profiles += iprofiles

        if offset >= icount or offset >= 999: break

        offset += max_facet_values

        if offset >= 1000: offset = 999

    return profiles

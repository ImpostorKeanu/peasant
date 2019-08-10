from Peasant.profile import Profile

def extractInfo(j):
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
    return result_count,[extractProfile(e) for e in j['elements']]

def extractProfile(jelement):
    '''Derive and return  Peasant.profile object from an element.
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

    # return a Peasant.profile object
    return Profile(first_name,last_name,occupation,
            public_identifier,industry,location)

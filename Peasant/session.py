import requests
import re
from types import MethodType
from Peasant.generic import *
from Peasant.parsers import *
from Peasant.suffix_printer import *
from Peasant.basic_profile import BasicProfile
from Peasant.exceptions import *
from Peasant.extractors import *
from Peasant.picture import *
from Peasant.image import Image
from Peasant.constants import *
from Peasant.decorators import *
import pdb

class Session(requests.Session):
    '''Custom session object to ease the process of passing
    headers and other variables when making requests.
    '''

    def __init__(self,base_url='https://www.linkedin.com',
            proxies=None,verify=True,headers=None,
            *args,**kwargs):
        
        # Perform initial initializations
        super().__init__(*args,**kwargs)

        # Set instance variables
        proxies = {} or proxies
        headers = {} or headers
        self.proxies=proxies
        self.verify=verify
        self.headers.update(headers)
        self.base_url=base_url
        self.authenticated=False
        
        # Pre-configure necessary API headers
        self.addAPIHeaders()
    
    def proxyRequest(self, method, path, *args, **kwargs):
        '''Proxy a request to `requests.Session` while passing
        all necessary arguments to assure that headers and other
        values are set properly.
        '''

        # Update request headers
        if 'headers' in kwargs:
            self.headers.update(kwargs['headers'])
            del(kwargs['headers'])

        # Update the base URL if needed
        if 'url' in kwargs and kwargs['url'] == self.base_url:
            del(kwargs['url'])

        # Assure the current path ends with a slash
        if not path[0] == '/': path = '/'+path

        return super(requests.Session,requests.Session) \
                .__getattribute__(requests.Session,method) \
                (self, self.base_url+path, proxies=self.proxies,
                verify=self.verify, *args, **kwargs)

    # ==========================================
    # METHODS SIMPLIFYING HTTP HEADER MANAGEMENT
    # ==========================================
    
    def removeAPIHeaders(self):
        '''Remove API headers for requests until `Session.addAPIHeaders`
        is called to add them back. This is useful in situations when
        non-API requests are sent to LinkedIn, such as when posting
        credentials.
        '''

        for k in ['Accept','x-restli-protocol-version','x-li-lang',
            'x-li-track']:

            del(self.headers[k])

    def addAPIHeaders(self):
        '''Add the API headers back to the `Session` object. Generally
        called at the end of a method when `Session.removeAPIHeaders`
        has been called.
        '''

        self.headers.update(
            {
                'Accept':ACCEPT_VND_NORMALIZED_JSON_21,
                'x-restli-protocol-version':'2.0.0',
                'x-li-lang':'en_US',
                'x-li-track':'{"clientVersion":"1.5.*","osName":' \
                    '"web","timezoneOffset":-5,"deviceFormFactor":'\
                    '"DESKTOP","mpName":"voyager-web"}'
            }
        )

    def removeAcceptHeader(self):
        '''Remove the JSON accept header from the Session object. Useful
        in situations when basic variations of API responses are desired,
        which often contain different outputs than that of the 2.1 version.
        '''

        if 'Accept' in self.headers:
            del(self.headers['Accept'])

    def addAcceptHeader(self,value=ACCEPT_VND_NORMALIZED_JSON_21):
        '''Add the JSON accept header back to the Session object.
        '''

        self.headers.update({'Accept':value})

    # ====================
    # HTTP REQUEST METHODS
    # ====================
    
    def get(self,*args,**kwargs):
        '''Override the get method to use `Session.proxyRequest`.
        '''

        return self.proxyRequest('get',*args,**kwargs)
    
    def post(self,*args,**kwargs):
        '''Override the post method to use `Session.proxyRequest`.
        '''

        return self.proxyRequest('post',*args,**kwargs)

    def delete(self,*args,**kwargs):
        '''Override the delete method to use `Session.proxyRequest`.
        '''

        return self.proxyRequest('delete',*args,**kwargs)

    # ======================
    # AUTHENTICATION METHODS
    # ======================

    def cookieAuth(self,cookies,*args,**kwargs):
        '''Accept a string representing cookies and inject them
        into the `Session` object for future authentication. This
        method will verify if the credentials are valid by making
        a request to `/voyager/api/me` and validating the response
        code, where any value that is not 200 indicates that the
        cookies are invalid.
        '''

        requests.utils.add_dict_to_cookiejar(self.cookies,
                parseCookiesString(cookies)
            )

        self.headers.update(
            {
                'csrf-token':parseJSESSIONID(
                        self.cookies.get('JSESSIONID')
                    )
            }
        )

        profile = self.getBasicProfile(*args,**kwargs)

        self.authenticated = True

        return profile
    
    def credentialAuth(self,credentials,*args,**kwargs):
        '''Accept colon-delimited credentials and perform
        authentication to LinkedIn using a call to
        `Session.postLogin`.
        '''
    
        return self.postLogin(*parseCredentials(credentials))

    def userPassAuth(self,username,password,*args,**kwargs):
        '''Accept a username and password and perform
        authentication to LinkedIn using a call to
        `Session.postLogin`.
        '''

        return self.postLogin(username,password)

    # =====================
    # LINKEDIN CAPABILITIES
    # =====================

    def getBasicProfile(self):
        '''Get basic profile information.
        '''

        path = '/voyager/api/me'

        # Try to request current profile info. If a status code
        # other than 200 is received, we know the cookies are
        # invalid

        try:
            resp = self.get(path)
        except Exception as e:
            wsprint('Failed to request basic profile information')
            raise e

        checkStatus(resp.status_code,200,
            'Failed to get basic profile. This suggests ' \
            'invalid credentials or stale cookies.'
        )

        # ====================
        # PARSING THE RESPONSE
        # ====================


        js = resp.json()
        for obj in js['included']:
            if 'firstName' in obj and 'lastName' in obj:
                break

        for k in list(obj.keys()):
            if k.startswith('$'): del(obj[k])

        # ===============================
        # CREATING A BASIC PROFILE OBJECT
        # ===============================

        try:

            return BasicProfile(**obj,
                    premiumSubscriber=js['data']['premiumSubscriber'])

        except Exception as e:

            wsprint(
                'Failed to generated BasicProfile from JSON response'
            )
            raise e

    @is_authenticated
    def getCurrentPublicIdentifier(self,*args,**kwargs):
        '''Get the public identifier for the account
        which the session object is currently authenticated
        as.
        '''

        path = '/voyager/api/me'
        obj = self.get(path,*args,**kwargs).json()

        if 'included' not in obj or not obj['included']:
            raise SessionException(
                'Failed to obtain current profile information'
            )

        try:
            return obj['included'][0]['publicIdentifier']
        except Exception as e:
            wsprint(
                'Failed to parse public identifier from JSON response'
            )
            raise e

    @is_authenticated
    def getCurrentProfileIdentifiers(self,*args,**kwargs):
        '''Get key identifiers associated with the current profile: 
        `publicIdentifier`, `trackingId`, and `entityUrn`.
        '''

        obj = self.getCurrentProfile(*args,**kwargs)['included'][0]

        try:

            return id_dict(obj['trackingId'],
                    obj['publicIdentifier'],
                    obj['entityUrn'])

        except Exception as e:

            wsprint(
                'Failed to parse profile identifiers from JSON response'
            )
            raise e

    @is_authenticated
    def getProfile(self,public_identifier,basic=False):
        '''Get a profile by public identifier.
        '''

        path = '/voyager/api/identity/dash/profiles'

        if basic: self.removeAcceptHeader()

        try:

            obj = self.get(path+'?q=memberIdentity&memberIdentity='+ \
                public_identifier+'&decorationId=com.linkedin.' \
                'voyager.dash.deco.identity.profile.FullProfileWithEnt' \
                'ities-35').json()

        except Exception as e:

            wsprint(
                'Failed to get JSON response from LinkedIn API'
            )

        if basic: self.addAcceptHeader()

        return obj

    @is_authenticated
    def getCurrentProfile(self,*args,**kwargs):
        '''Get the profile for the account which the session
        object is currently authenticated as.
        '''

        ids = self.getCurrentProfileIdentifiers(*args,**kwargs)

        try:
            return self.getProfile(ids.publicIdentifier,*args,**kwargs)
        except Exception as e:
            wsprint(
                'Failed to get the profile for current session'
            )
            raise e

    @is_authenticated
    def getLogout(self,*args,**kwargs):
        '''Terminate the current session, releasing the session
        cookies.
        '''

        path = '/uas/logout'
        params = {
                'session_redirect':'/voyager/loginRedirect.html',
                'csrfToken':parseCsrf(self.cookies['JSESSIONID'])
            }

        try:

            return self.get(path,
                params=params,
                allow_redirects=False,
                *args,**kwargs)

        except Exception as e:

            wsprint(
                'Logout failed'
            )
            raise e

    @is_authenticated
    def getCurrentFsdProfileURN(self,*args,**kwargs):
        '''Get the FSD Profile URN for the current profile.
        '''

        obj = self.getCurrentProfile(*args,**kwargs)


        try:
            return obj['included'][0]['entityUrn'] \
                .split(':')[-1]
        except Exception as e:
            wsprint(
                'Failed to obtain the entityUrn for the current profile',
            )
            raise(e)

    @is_authenticated
    def getVersionTag(self,urn=None,*args,**kwargs):
        '''Get the current version tag for the current
        profile.
        '''

        if not urn:
            urn = self.getBasicProfile(*args,**kwargs) \
                    .entityUrnId

        path = f'/voyager/api/identity/profiles/{urn}/versionTag'

        try:
            return self.get(path,*args,**kwargs) \
                    .json()['data']['versionTag']
        except Exception as e:
            wsprint(
                'Failed to get the current version tag for the ' \
                'current profile.')
            raise e

    @is_authenticated
    def getTrackingId(self,*args,**kwargs):
        '''Get the current tracking id for the current
        profile.
        '''

        try:
            return self.getBasicProfile(*args,**kwargs) \
                    .trackingId
        except Exception as e:
            wsprint('Failed to get the current tracking id for the ' \
                    'current profile.')

    @is_authenticated
    @versionize
    def postBasicProfileUpdate(self,payload,params,
            current_profile_urn=None):
        '''Update the basic information of the current profile, such
        as the full name and headline.
        '''

        if not current_profile_urn:
            current_profile_urn = self.getBasicProfile() \
                .entityUrnId

        path = '/voyager/api/identity/dash/profiles/' \
               f'urn:li:fsd_profile:{current_profile_urn}'

        data={'patch':{'$set':payload}}

        try:

            resp = self.post(path,json=data,params=params)

        except Exception as e:

            wsprint(
                'Failed to post basic profile update'
            )
            raise e

        checkStatus(resp.status_code,202,
                'Profile update failed')

        return True

    @is_authenticated
    def spoofBasicInfo(self,public_identifier):
        '''Spoof basic profile information from profile identified
        via the public_identifier.
        '''

        try:
            raw_profile = rp = self.getProfile(public_identifier,
                    basic=True)['elements'][0]
        except Exception as e:
            wsprint('Failed to get profile by public_identifier! Check the ' \
                'identifier and try again.')
            raise(e)

        obj = {k:v for k,v in rp.items() if k.startswith('multiLocale')}
        resp = self.postBasicProfileUpdate(obj)

        return resp


    @is_authenticated
    def spoofExperience(self,public_identifier):
        '''Spoof all experience records from a target profile.

        - public_identifier - `str` - public profile identifier
        '''

        key_blacklist = ['companyName','description','title',
                'locationName','geoUrn','geoLocationName',
                'multiLocaleGeoLocationName','authority',
                'name']

        def additional_checks(inc):
            return checkEntityUrn(inc,'urn:li:fsd_profilePosition')

        try:

            return self.spoofLoop(public_identifier,
                    indicators=['companyUrn'],
                    method=self.postNewExperience,
                    key_blacklist=key_blacklist,
                    additional_checks=additional_checks)

        except Exception as e:

            wsprint(
                'Failed to loop over spoofed content when ' \
                'spoofing experience'
            )
            raise e

    @is_authenticated
    def spoofEducation(self,public_identifier):
        '''Accept a target public identifier and spoof all education
        records to the current profile.

        - returns a list of response objects
        '''

        key_blacklist = ['degreeName','schoolName','fieldOfStudy',
                'grade','description','activities']

        def additional_checks(inc):
            return checkEntityUrn(inc,'urn:li:fsd_profileEducation')

        try:
        
            return self.spoofLoop(public_identifier,
                    indicators=['schoolUrn'],
                    method=self.postNewEducation,
                    key_blacklist=key_blacklist,
                    additional_checks=additional_checks)

        except Exception as e:

            wsprint(
                'Failed to loop over spoofed content when spoofing ' \
                'education'
            )

            raise e

    # TODO: Complete certificate spoofing
    # - neet to complete deletion method
    @is_authenticated
    def spoofCertification(self,public_identifier):

        key_blacklist = []

        def additional_checks(inc):
            return checkEntityUrn(inc,'urn:li:fsd_profileCertification')

        try:

            return self.spoofLoop(public_identifier,
                indicators=['companyUrn'],
                method=self.postNewCertification,
                key_blacklist=key_blacklist,
                additional_checks=additional_checks)

        except Exception as e:

            wsprint(
                'Failed to loop over spoofed content when spoofing ' \
                'certifications'
            )
            raise e

    def spoofLoop(self,public_identifier,indicators,method,
            key_blacklist=[],additional_checks=None):
        '''Loop over all "included" objects in the response
        of a profile object and spoof the content back to the
        current target profile.
        '''

        assert indicators.__class__ == list,(
            'indicators argument must be a list of strings'
        )

        assert key_blacklist.__class__ == list,(
            'blacklist argument must be a list of strings'
        )

        assert method.__class__ == MethodType,(
            'method must be a method'
        )

        # Get the current profile
        raw_profile = rp = self.getProfile(public_identifier)

        # Iterate over each included, tracking each response
        # object
        responses, posted = [], {}
        for inc in rp['included']:

            # Assure all indicators are in the target object
            for indicator in indicators:

                # Skip it if not
                if not indicator in inc:
                    inc = None
                    break

            # Duplicate the object back to the target profile
            # inc is not None
            if inc:

                inc = filterDict(inc,key_blacklist)

                if additional_checks and not additional_checks(inc):
                    continue

                if 'entityUrn' in inc: del(inc['entityUrn'])

                filtered = filterDict(inc,key_blacklist)

                # =====================================
                # PREVENT DUPLICATE POSTS OF EXPERIENCE
                # =====================================

                if 'companyUrn' in inc and inc['companyUrn'] in posted:

                    if 'dateRange' in inc and inc['dateRange'] in posted[inc['companyUrn']]:
                                continue
                    else:

                        posted[inc['companyUrn']].append(inc['dateRange'])
                else:

                    if 'companyUrn' in inc and 'dateRange' in inc:

                        posted[inc['companyUrn']] = [inc['dateRange']]
        
                # TODO: Invalid date ranges break things
                # omitting for the time being. Additional
                # research/development needed.
                try:

                    responses.append(
                        method(filtered)
                    )

                except AssertionError:

                    if 'dateRange' in inc:

                        if inc['dateRange']['end']['year'] > CYR:
                            inc['dateRange']['end']['year'] = CYR

                        if inc['dateRange']['end']['month'] > CMO:
                            if CMO == 1:
                                inc['dateRange']['end']['year'] = CYR-1
                                inc['dateRange']['end']['month'] = 12
                            else:
                                inc['dateRange']['end']['month'] = CMO-1
                    
                        responses.append(
                            method(filtered)
                        )

                    else:

                        raise AssertionError('Failed to update profile!')

        return responses

    @is_authenticated
    @versionize
    def postNewCertification(self,data,params):

        path = '/voyager/api/identity/dash/profileCertifications'

        try:
            resp = self.post(path,json=data,params=params)
        except Exception as e:
            wsprint(
                'Failed to post new certification content to current ' \
                'profile.'
            )
            raise e

        checkStatus(resp.status_code,201,
                'Failed to create new certificateion')

        return resp

    @is_authenticated
    @versionize
    def postNewEducation(self,data,params):
        '''Create a new educate for the current profile.

        - returns a response object
        - raises assertion error should a response with
        status code other than 201 be detected

        # Expected Input Object

        {
            "dateRange": {
                "start": {
                    "year": 2002
                },
                "end": {
                    "year": 2006
                }
            },
            "multiLocaleSchoolName": {
                "en_US": "Rice University"
            },
            "schoolUrn": "urn:li:fsd_school:19472",
            "multiLocaleFieldOfStudy": {
                "en_US": "Economics, Political Science"
            },
            "multiLocaleDegreeName": {
                "en_US": "Bachelor of Arts (B.A.)"
            }
        }

        '''

        path = '/voyager/api/identity/dash/profileEducations'

        try:
            resp = self.post(path,json=data,params=params)
        except Exception as e:
            wsprint(
                'Failed to post new education content to current ' \
                'profile.'
            )
            raise e

        checkStatus(resp.status_code,201,
                'Failed to create new education')

        return resp

    @is_authenticated
    @versionize
    def postNewExperience(self,data,params):

        path = '/voyager/api/identity/dash/profilePositions'

        try:
            resp = self.post(path,json=data,params=params)
        except Exception as e:
            wsprint(
                'Failed to post new experience for current profile'
            )
            raise e

        checkStatus(resp.status_code,201,
                'Failed to create new experience')

        return resp

    @is_authenticated
    @versionize
    def versionizedRequest(self,path,params,method,*args,**kwargs):
        '''Make a request configured with versioning parameters
        required by LinkedIn. This will incorporate the `versionTag`
        query parameter and the `trackingId` in the
        `x-li-page-instance` HTTP header.
        '''

        try:

            return self.__getattribute__(method)(path,params=params,
                    *args,**kwargs)

        except Exception as e:

            wsprint(
                'Failed to make a versionized request'
            )

            raise e

    @is_authenticated
    def deleteEducation(self):
        '''Delete all education records from the current profile.

        - returns a list of response objects
        - raises an assertion error should a response with a status
        code that isn't 204 be returned
        '''

        path = '/voyager/api/identity/dash/profileEducations'
        basic_profile = self.getBasicProfile()
        raw_profile = self.getProfile(basic_profile.publicIdentifier)

        responses = []
        for i in raw_profile['included']:

            if 'schoolUrn' in i and \
                    not '*profilePositionInPositionGroup' in i:

                p = path+'/'+i['entityUrn']

                try:

                    resp = self.versionizedRequest(path=p,
                        method='delete')

                except Exception as e:

                    wsprint(
                        'Failed to delete education from current profile'
                    )
                    raise e

                checkStatus(resp.status_code,204,
                        'Failed to delete education') 

                responses.append(resp)

        return responses

    @is_authenticated
    def deleteExperience(self):
        '''Delete all experience from current profile.
        '''

        path = '/voyager/api/identity/dash/profilePositions'
        basic_profile = self.getBasicProfile()
        raw_profile = self.getProfile(basic_profile.publicIdentifier)

        responses = []
        for i in raw_profile['included']:

            if 'companyUrn' in i and \
                    not '*profilePositionInPositionGroup' in i:

                p = path+'/'+i['entityUrn']

                resp = self.versionizedRequest(path=p,
                    method='delete')

                try:

                    checkStatus(resp.status_code,204,
                            'Failed to delete experience')

                except Exception as e:

                    wsprint(
                        'Failed to delete experience from current profile'
                    )
                    raise e

                responses.append(resp)

        return responses

    def postLogin(self,username,password,*args,**kwargs):
        self.removeAPIHeaders()
        self.get('/login')
        try:
            # TODO: Reckless parsing of csrf_param value here
            csrf_param = re.search('&(.+)"',self.cookies.get('bcookie')) \
                    .groups()[0]
        except Exception as e:
            wsprint('Failed to get CSRF param from initial request ' \
                    'to /login. This suggests the login process has ' \
                    'been changed by LinkedIn')
            raise e

        resp = self.post('/checkpoint/lg/login-submit',
                    data={
                        'session_key':username,
                        'session_password':password,
                        'loginCsrfParam':csrf_param
                    },
                    *args,**kwargs
                )
    
        try:
            self.headers.update(
                {
                    'csrf-token':parseJSESSIONID(
                            self.cookies.get('JSESSIONID')
                        ),
                }
            )
        except:
            wsprint('Invalid credentials provided. JSESSIONID not ' \
                    'found in response.')
    
        # Determine success
        if resp.status_code != 200 or not resp.request.url.endswith('feed/'):
            raise SessionException('Invalid credentials supplied')

        self.authenticated = True
        self.addAPIHeaders()

        return True

    @is_authenticated
    def getCompanyId(self,company_name,*args,**kwargs):
        '''Use the voyager API to obtain the identifier associated with
        a given company name.
        '''

        # ==============
        # BUILD THE PATH
        # ==============

        path = '/voyager/api/organization/updatesV2'
        params = {
                'companyIdOrUniversalName':company_name,
                'count':25,
                'moduleKey':'ORGANIZATION_MEMBER_FEED_DESKTOP',
                'q':'companyRelevanceFeed'
                }
        
        # ===================================
        # MAKE THE REQUEST AND PARSE OUT JSON
        # ===================================

        try:

            obj = self.get(path,params=params,*args,**kwargs).json()
        except Exception as e:
            wsprint(
                'Failed to make request for the company id'
            )
            raise e

        if 'status' in obj and obj['status'] == 404:
            raise SessionException(
                f'Failed to get company id for {company_name}'
            )

        # =================================================
        # ITERATE OVER EACH INCLUDED RESPONSE & EXTRACT CID
        # =================================================
        
        cid = None
        for inc in obj['included']:

            if 'universalName' in inc and \
                    inc['universalName'] == company_name:

                cid = inc['objectUrn'].split(':')[-1]

        # Raise an exception when extraction of the CID fails
        if not cid:
            raise SessionException('Company identifier not found by name')

        return cid

    @is_authenticated
    def postConnectionRequest(self,urn,
            tracking_id="86us0JMVTy6fXUztPyFKhw==",
            message=None,
            *args,**kwargs):
        '''Forge a connection request for a given member, as identified
        by URN.
        '''

        path = '/voyager/api/growth/normInvitations'
        data = {
                "emberEntityName":"growth/invitation/norm-invitation",
                "invitee":{
                    "com.linkedin.voyager.growth.invitation.InviteeProfile":{
                        "profileId":urn
                        }
                    },
                "trackingId":tracking_id}

        if message: data['message'] = message

        try:

            return self.post(path,json=data,*args,**kwargs)

        except Exception as e:

            wsprint(
                'Failed to post connection request'
            )
            raise e

    @is_authenticated
    def getContactSearchResults(self,company_id,start,
            max_facet_values=10,*args,**kwargs):

        if self.headers.get('Accept'): del(self.headers['Accept'])

        path = '/voyager/api/search/hits?count=12' \
            f'&facetCurrentCompany=List({company_id})' \
            f'&maxFacetValues={max_facet_values}' \
            f'&origin=organization&q=people&start={start}' \
            '&supportedFacets=List(GEO_REGION,SCHOOL,CURRENT_COMPANY,' \
            'CURRENT_FUNCTION,FIELD_OF_STUDY,SKILL_EXPLICIT,NETWORK)'

        try:

            return self.get(path,*args,**kwargs)

        except Exception as e:

            wsprint(
                'Failed to get contact search results'
            )
            raise e

    @is_authenticated
    def getProfileImages(self,public_identifier):

        path = f'/voyager/api/identity/profiles/{public_identifier}'
        
        try:
            obj = self.get(path).json()
        except Exception as e:
            wsprint(
                'Failed to get profile images'
            )
            raise e

        if not 'included' in obj:
            return None

        for inc in obj['included']:
            if 'firstName' in inc and 'lastName' in inc:
                break

        profile_pictures = []
        if 'picture' in inc and inc['picture'] and 'artifacts' in \
                inc['picture']:

            profile_pictures = extractImages(
                inc['picture']['rootUrl'],
                inc['picture']['artifacts'],
                self
            )

        background_images = []
        if 'backgroundImage' in inc and inc['backgroundImage'] and \
                'artifacts' in inc['backgroundImage']:

                background_images = extractImages(
                    inc['backgroundImage']['rootUrl'],
                    inc['backgroundImage']['artifacts'],
                    self
                )

        return profile_pictures,background_images


    @is_authenticated
    def spoofPictures(self,public_identifier,
            profile=True,background=True):
        '''Spoof pictures from a profile identified by
        `public_identifier`.
        '''

        profile_pictures, background_pictures = \
                self.getProfileImages(public_identifier)

        if profile and profile_pictures:

            original_url,original_urn = \
                self.postMediaUploadMetadata(
                    profile_pictures.largest,
                    'PROFILE_ORIGINAL_PHOTO'
                )

            display_url,display_urn = \
                self.postMediaUploadMetadata(
                    profile_pictures.largest,
                    'PROFILE_DISPLAY_PHOTO'
                )

            self.putImageUpload(original_url,profile_pictures.largest)
            self.putImageUpload(display_url,profile_pictures.largest)

            self.postApplyImageChange('profilePicture',original_urn,
                    display_urn)

        if background and background_pictures:
            
            original_url,original_urn = \
                self.postMediaUploadMetadata(
                    background_pictures.largest,
                    'PROFILE_ORIGINAL_BACKGROUND'
                )

            display_url,display_urn = \
                self.postMediaUploadMetadata(
                    background_pictures.largest,
                    'PROFILE_DISPLAY_BACKGROUND'
                )

            self.putImageUpload(original_url,background_pictures.largest)
            self.putImageUpload(display_url,background_pictures.largest)

            self.postApplyImageChange('backgroundPicture',original_urn,
                    display_urn)

    @is_authenticated
    def postMediaUploadMetadata(self,image,media_upload_type):
        '''Get a single use upload URL and URN for an image
        that will be uploaded.
        '''

        assert media_upload_type in MEDIA_UPLOAD_DISPLAY_TYPES,(
            'media_upload_type argument must be one of the following: '+\
            ' ,'.join(MEDIA_UPLOAD_DISPLAY_TYPES)
        )
            
        path = '/voyager/api/voyagerMediaUploadMetadata'
        params = {'action':'upload'}

        # ==================================
        # MAKE THE REQUEST FOR THE URLS/URNs
        # ==================================

        try:

            resp = self.post(path,
                    params=params,
                    json={'mediaUploadType':media_upload_type,
                        'filesize':image.size}
                    )

        except Exception as e:

            esprint('Failed to make request for image upload URLs')
            raise(e)

        if resp.status_code != 200:
            raise SessionException(
                'Failed to obtain image upload URLs'
            )

        # ==================
        # PARSE THE RESPONSE
        # ==================

        obj = resp.json()

        # Get the upload URL and digitalmediaAssetURN
        try:
            singleUploadUrl = obj['data']['value']['singleUploadUrl']
            digitalmediaAssetUrn = obj['data']['value']['urn']
        except Exception as e:
            esprint('Failed to parse URL and URN for images',suf='[!]')
            raise e

        return singleUploadUrl,digitalmediaAssetUrn

    @is_authenticated
    def putImageUpload(self,url,image,media_type_family='STILLIMAGE'):
        '''Upload an image using a URL obtained via
        `session.postMediaUploadMetadata`.
        '''

        assert image.__class__ == Image,(
            'image argument must be of type Image'
        )

        # ===========================
        # UPDATE HEADERS AND PUT DATA
        # ===========================


        try:
            self.headers.update({'media-type-family':media_type_family})
            resp = self.put(url,data=image.read())
        except Exception as e:
            wsprint(
                'Failed up put image upload while spoofing images'
            )
            raise e
        finally:
            del(self.headers['media-type-family'])
        
        checkStatus(resp.status_code,201,
            'Failed to upload image')

        image.seek(0)

        return resp

    @is_authenticated
    @versionize
    def postApplyImageChange(self,image_type,original_image_urn,
            display_image_urn,params):

        # ==================================================
        # ASSERT IMAGE URN FORMATS TO AVOID FUTURE CONFUSION
        # ==================================================

        assert image_type in ['profilePicture','backgroundPicture'],(
            'image_type argument must be profilePicture or ' \
            'backgroundPicture'
        )

        assert re.match(URN_RE,display_image_urn),(
            'image_urn argument should be in this format: ' \
            'urn:li:digitalmedia Asset:XXXXXXXXXXXXXXXXX')
        
        assert re.match(URN_RE,original_image_urn),(
            'original_image_urn argument should be in this format: ' \
            'urn:li:digitalmedia Asset:XXXXXXXXXXXXXXXXX')

        # ======================================
        # CONSTRUCT URL WITH CURRENT PROFILE URN
        # ======================================

        basic_profile = bp = self.getBasicProfile()
        path = '/voyager/api/identity/normProfiles/' \
               f'{bp.entityUrnId}'

        data = {
                'patch': {
                    image_type: {
                        '$set': {
                            'originalImage': original_image_urn,
                            'displayImage': display_image_urn
                            }
                        }
                    }
                }

        # ========================================
        # MAKE THE REQUEST AND RETURN THE RESPONSE
        # ========================================

        try:

            resp = self.post(path,json=data,params=params)

        except Exception as e:

            wsprint('Failed to post image application configuration')
            raise(e)

        checkStatus(resp.status_code,202,
                'Failed to apply profile picture configuration')

        return resp


    # TODO: Finish this...potential source of information
    @is_authenticated
    def getProfileContactInfo(self,urn):
        '''Get profile contact information, including

        - Twitter Handles
        - WeChat
        - Email Address
        - Websites

        # Response Payload

            {
                "data": {
                    "birthDateOn": null,
                    "birthdayVisibilitySetting": null,
                    "address": null,
                    "weChatContactInfo": null,
                    "primaryTwitterHandle": null,
                    "twitterHandles": [],
                    "phoneNumbers": null,
                    "ims": null,
                    "$type": "com.linkedin.voyager.identity.profile.ProfileContactInfo",
                    "emailAddress": "***********@comcast.net",
                    "entityUrn": "urn:li:fs_contactinfo:************",
                    "connectedAt": 1574489700000,
                    "websites": null,
                    "sesameCreditGradeInfo": null,
                    "interests": null
                },
                "included": []
            }
        '''

        path = f'/voyager/api/identity/profiles/{urn}/' \
                'profileContactInfo'

        try:
            return self.get(path).json()['data']
        except Exception as e:
            wsprint('Failed to get contact information')
            raise e

    def login(self,args):
        '''Accepts args object and perform authentication relative to
        supplied arguments.
        '''

        if args.cookies:

            cookies = importCookies(args.cookies)

            return self.cookieAuth(cookies)

        elif args.credentials:

            return self.credentialAuth(args.credentials)

        else:

            esprint('Credentials not provided. Enter credentials to ' \
                    'continue')
            return self.userPassAuth(*getCredentials())

import requests
import pdb
from IPython import embed
from Peasant.generic import *
from Peasant.parsers import *
from Peasant.suffix_printer import *
from Peasant.basic_profile import BasicProfile
from Peasant.exceptions import *
from functools import wraps
from types import MethodType
from datetime import datetime

NOW = datetime.now()
CYR = CURRENT_YEAR  = NOW.year
CMO = CURRENT_MONTH = NOW.month

def checkEntityUrn(inc,start):

    if 'entityUrn' in inc and \
            inc['entityUrn'].startswith(start):
        return True
    else:
        return False

# WARNING: Method decorator
def is_authenticated(method):
    '''Assure that the `Session` object is authenticated
    before executing a given method.
    '''

    @wraps(method)
    def inner(session, *args, **kwargs):

        # Throw an assertion error should the session not yet be
        # authenticated
        assert session.authenticated, ('The session object must be ' \
            f'authenticated prior calling session.{method.__name__}')

        # Execute the method and return the output
        return method(session, *args, **kwargs)

    return inner

# WARNING: Method decorator
def versionize(method):
    '''Inject a `x-li-page-instance` header into the
    request, as required by LinkedIn when particular
    changes are being applied to the profile.
    '''

    @wraps(method)
    def inner(session,*args,**kwargs):

        # Update headers with x-li-page-instance header
        session.headers.update(
                {'x-li-page-instance':'urn:li:page:d_fl' \
                'agship3_profile_self_edit_top_card;' + \
                session.getTrackingId()}
            )

        # Add versionTag to query parameters
        if 'params' in kwargs:
            kwargs['params']['versionTag'] = self.getVersionTag()
        else:
            kwargs['params'] = {'versionTag':session.getVersionTag()}

        # Execute the method
        ret = method(session, *args, **kwargs)

        # Delete the x-li-page-instance header
        del(session.headers['x-li-page-instance'])

        return ret

    return inner

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
        self.headers.update(
            {
                'Accept':'application/vnd.linkedin.normalized+json+2.1',
                'x-restli-protocol-version':'2.0.0',
                'x-li-lang':'en_US',
                'x-li-track':'{"clientVersion":"1.5.*","osName":' \
                    '"web","timezoneOffset":-5,"deviceFormFactor":'\
                    '"DESKTOP","mpName":"voyager-web"}'
            }
        )

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
    
    def removeAcceptHeader(self):
        '''Remove the JSON accept header from the Session object.
        '''

        if 'Accept' in self.headers:
            del(self.headers['Accept'])

    def addAcceptHeader(self,version='2.1'):
        '''Add the JSON accept header back to the Session object.
        '''

        header = 'application/vnd.linkedin' \
                '.normalized+json'

        if version: header += '+'+version
        self.headers.update({'Accept':header})
    
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

    @is_authenticated
    def getBasicProfile(self):
        '''Get basic profile information.
        '''

        path = '/voyager/api/me'

        # Try to request current profile info. If a status code
        # other than 200 is received, we know the cookies are
        # invalid
        resp = self.get(path)
        if resp.status_code != 200:
            raise SessionException(
                    'Failed to get basic profile. This suggests ' \
                    'invalid credentials or stale cookies.'
                )

        js = resp.json()
        for obj in js['included']:
            if 'firstName' in obj and 'lastName' in obj:
                break

        for k in list(obj.keys()):
            if k.startswith('$'): del(obj[k])

        return BasicProfile(**obj,
                premiumSubscriber=js['data']['premiumSubscriber'])

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
        
        return obj['included'][0]['publicIdentifier']

    @is_authenticated
    def getCurrentProfileIdentifiers(self,*args,**kwargs):
        '''Get key identifiers associated with the current profile: 
        `publicIdentifier`, `trackingId`, and `entityUrn`.
        '''

        obj = getCurrentProfile(*args,**kwargs)['included'][0]

        return id_dict(obj['trackingId'],
                obj['publicIdentifier'],
                obj['entityUrn'])

    @is_authenticated
    def getProfile(self,public_identifier,basic=False):
        '''Get a profile by public identifier.
        '''

        path = '/voyager/api/identity/dash/profiles'

        if basic: self.removeAcceptHeader()

        obj = self.get(path+'?q=memberIdentity&memberIdentity='+ \
                public_identifier+'&decorationId=com.linkedin.' \
                'voyager.dash.deco.identity.profile.FullProfileWithEnt' \
                'ities-35').json()

        if basic: self.addAcceptHeader()

        return obj

    @is_authenticated
    def getCurrentProfile(self,*args,**kwargs):
        '''Get the profile for the account which the session
        object is currently authenticated as.
        '''

        ids = self.getCurrentProfileIdentifiers(*args,**kwargs)
        return self.getProfile(ids.publicIdentifier,*args,**kwargs)

    @is_authenticated
    def getLogout(self,*args,**kwargs):
        path = '/uas/logout'
        params = {
                'session_redirect':'/voyager/loginRedirect.html',
                'csrfToken':parseCsrf(self.cookies['JSESSIONID'])
            }

        return self.get(path,params=params,allow_redirects=False,
                *args,**kwargs)

    @is_authenticated
    def getCurrentFsdProfileURN(self,*args,**kwargs):
        '''Get the FSD Profile URN for the current profile.
        '''

        obj = self.getCurrentProfile(*args,**kwargs)


        try:
            return obj['included'][0]['entityUrn'] \
                .split(':')[-1]
        except:
            pass

        raise AssertionError(
            'Failed to extract current profile entityUrn'
        )

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
            raise AssertionError('Failed to get versionTag')

    @is_authenticated
    def getTrackingId(self,*args,**kwargs):
        '''Get the current tracking id for the current
        profile.
        '''

        return self.getBasicProfile(*args,**kwargs) \
                .trackingId

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

        resp = self.post(path,json=data,params=params)

        checkStatus(resp.status_code,202,
                'Profile update failed')

        return True

    @is_authenticated
    def spoofProfile(self,public_identifier):
        '''Silently spoof the entirety of a target profile.
        
        - public_identifier - `str` - public profile identifier
        '''

        raw_profile = rp = self.getProfile(public_identifier,basic=True) \
                ['elements'][0]

        obj = {k:v for k,v in rp.items() if k.startswith('multiLocale')}

        self.postBasicProfileUpdate(obj)
        self.deleteEducation()
        self.spoofEducation(public_identifier)
        self.deleteExperience()
        self.spoofExperience(public_identifier)

        return True

    @is_authenticated
    def spoofBasicInfo(self,public_identifier):
        '''Spoof basic profile information from profile identified
        via the public_identifier.
        '''

        raw_profile = rp = self.getProfile(public_identifier,basic=True) \
                ['elements'][0]
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

        return self.spoofLoop(public_identifier,
                indicators=['companyUrn'],
                method=self.postNewExperience,
                key_blacklist=key_blacklist,
                additional_checks=additional_checks)

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
        
        return self.spoofLoop(public_identifier,
                indicators=['schoolUrn'],
                method=self.postNewEducation,
                key_blacklist=key_blacklist,
                additional_checks=additional_checks)

    # TODO: Complete certificate spoofing
    # - neet to complete deletion method
    @is_authenticated
    def spoofCertification(self,public_identifier):

        key_blacklist = []

        def additional_checks(inc):
            return checkEntityUrn(inc,'urn:li:fsd_profileCertification')

        return self.spoofLoop(public_identifier,
                indicators=['companyUrn'],
                method=self.postNewCertification,
                key_blacklist=key_blacklist,
                additional_checks=additional_checks)

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
        responses = []
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
        
                # TODO: Invalid date ranges break things
                # omitting for the time being. Additional
                # research/development needed.
                try:

                    responses.append(
                        method(
                            filterDict(inc,key_blacklist)
                        )
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
                            method(
                                filterDict(inc,key_blacklist)
                             )
                        )

                    else:

                        raise AssertionError('Failed to update profile!')

        return responses

    @is_authenticated
    @versionize
    def postNewCertification(self,data,params):

        path = '/voyager/api/identity/dash/profileCertifications'
        resp = self.post(path,json=data,params=params)

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
        resp = self.post(path,json=data,params=params)

        checkStatus(resp.status_code,201,
                'Failed to create new education')

        return resp

    @is_authenticated
    @versionize
    def postNewExperience(self,data,params):

        path = '/voyager/api/identity/dash/profilePositions'
        resp = self.post(path,json=data,params=params)

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

        return self.__getattribute__(method)(path,params=params,
                *args,**kwargs)

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

                resp = self.versionizedRequest(path=p,
                        method='delete')

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

                checkStatus(resp.status_code,204,
                        'Failed to delete experience')

                responses.append(resp)

        return responses

    def postLogin(self,username,password,*args,**kwargs):
        self.get('/login')
        try:
            # TODO: Reckless parsing of csrf_param value here
            csrf_param = re.search('&(.+)"',self.cookies.get('bcookie')) \
                    .groups()[0]
        except Exception as e:
            raise SessionException('Failed to get CSRF param from initial request ' \
                    'to /login. This suggests the login process has ' \
                    'been changed by LinkedIn')

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
            esprint('Invalid credentials provided. JSESSIONID not ' \
                    'found in response.')
    
        # Determine success
        if resp.status_code != 200 or not resp.request.url.endswith('feed/'):
            raise SessionException('Invalid credentials supplied')

        self.authenticated = True

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

        obj = self.get(path,params=params,*args,**kwargs).json()

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

        return self.post(path,json=data,*args,**kwargs)

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

        return self.get(path,*args,**kwargs)

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
        except:
            raise AssertionError('Failed to get contact information')

    def postGeneralAccountUpdates(self,version_tag,tracking_id):

        path = '/voyager/api/identity/normProfiles/ACoAAC5X7EIBxyBuXK6eyHq6B4aK_2J8AP4XZcQ'
        params = {'versionTag':459105362}

        '''

        # Success Status: 202 Accepted


	# POST Body

            {
                "patch": {
                    "$set": {
                        "firstName": "First",
                        "lastName": "Name",
                        "headline": "Some Headline"
                    },
                    "location": {
                        "$set": {
                            "preferredGeoPlace": "urn:li:fs_city:(us,3-1-0-16-2)"
                        }
                    },
                    "miniProfile": {
                        "$set": {
                            "presence": {
                                "lastActiveAt": 1574158504000,
                                "availability": "ONLINE",
                                "instantlyReachable": false,
                                "$type": "com.linkedin.voyager.messaging.presence.MessagingPresenceStatus",
                                "lastFetchTime": 1574158504445
                            }
                        }
                    }
                }
            }
        '''

    def login(self,args):
        '''Accepts args object and perform authentication relative to
        supplied arguments.
        '''

        if args.cookies:

            return self.cookieAuth(args.cookies)

        elif args.credentials:

            return self.credentialAuth(args.credentials)

        else:

            esprint('Credentials not provided. Enter credentials to ' \
                    'continue')
            username,password = self.userPassAuth(getCredentials())
            return self.userPassAuth(username,password)

from Peasant.parsers import *
from Peasant.extractors import *
from Peasant.picture import *

class BasicProfile:
    '''A simple data structure representing the profile of
    the current user.
    '''

    def __init__(self,firstName,lastName,occupation,objectUrn,
            entityUrn,publicIdentifier,trackingId,
            premiumSubscriber=False,picture=None,
            backgroundImage=None,**kwargs):

        self.firstName = firstName
        self.lastName = lastName
        self.occupation = occupation
        self.objectUrn = objectUrn
        self.entityUrn = entityUrn # THIS URN IDENTIFIES PROFILE IN URIs
        self.publicIdentifier = publicIdentifier
        self.trackingId = trackingId
        self.objectUrnId = parseUrn(self.objectUrn)[1]
        self.entityUrnId = parseUrn(self.entityUrn)[1]
        self.premiumSubscriber = premiumSubscriber

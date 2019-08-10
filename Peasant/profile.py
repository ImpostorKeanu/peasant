class Profile:

    ATTRS = ['first_name','last_name','occupation','public_identifier',
            'industry','location']

    def __init__(self,first_name,last_name,occupation,public_identifier,
            industry,location):

        self.first_name = first_name
        self.last_name = last_name
        self.occupation = occupation
        self.public_identifier = public_identifier
        self.pid = self.public_identifier
        self.industry = industry
        self.location = location

    def __repr__(self):

        return f'< Profile: first_name:{self.first_name} ' \
               f'last_name:{self.last_name} ' \
               f'occupation:{self.occupation} >'

    def __eq__(self,other):

        if other.__class__ != Profile: return False
        return self.pid == other.pid

    def to_row(self):

        return [self.__getattribute__(a) for a in Profile.ATTRS]

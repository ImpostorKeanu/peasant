from Peasant.image import Image

class Picture:
    '''Object to represent a picture data structure receivede from
    the LinkedIn API.
    '''

    SIZES = ['small','medium','large','xlarge']
    RSIZES = list(reversed(SIZES))

    def __init__(self,small=None,medium=None,
            large=None,xlarge=None):

        # Assert that only Image objects are valid inputs
        # to the initializer
        for size in Picture.SIZES:
            assert locals()[size].__class__ == Image or \
                    locals()[size] == None,(
                f'{size} argument must be an Image object or None'
            )

        self.small = small
        self.medium = medium
        self.large = large
        self.xlarge = xlarge

    @property
    def largest(self):
        '''Return the image of the largest size.
        '''

        for s in Picture.RSIZES:
            i = self.__getattribute__(s)
            if i: return i

        return None

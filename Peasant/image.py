from io import BytesIO
import requests

class ImageException(Exception):
    pass

class Image(BytesIO):
    '''A `BytesIO` like object representing an image use to avoid
    having to write files to disk while spoofing images froma foreign
    LinkedIn profile.
    '''

    def __init__(self,size,url):
        
        self.size = size
        self.url = url
        self.http_response = None
        self.content = None
        self.data = self.content
        self.size = None

    def load(self,session):
            
        # Get the picture
        # NOTE: I call requests.get directly here because I
        # naively set the base URL to linkedin.com and images
        # are generally hosted on media.licdn.com.
        resp = requests.get(self.url,
                cookies=session.cookies.get_dict(),
                headers=session.headers,
                verify=session.verify,
                proxies=session.proxies)

        if resp.status_code != 200:
            raise ImageException(
                'Failed to download image'
            )

        self.http_response = resp
        self.content = resp.content
        self.size = self.content.__len__()
        self.write(resp.content)
        self.seek(0)

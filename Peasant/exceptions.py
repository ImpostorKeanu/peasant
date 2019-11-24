
class SessionException(Exception):
    pass

def checkStatus(status_code,valids,message=None,
        exception_class=SessionException):

    if valids.__class__ != list: valids = [valids]
    message = message or 'Invalid status code received'

    if status_code not in valids:
        raise exception_class(message)

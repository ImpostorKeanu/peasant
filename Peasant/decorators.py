from functools import wraps

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

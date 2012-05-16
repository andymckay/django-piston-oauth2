import oauth2 as oauth
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest


def get_oauth_request(request):
    """ Converts a Django request object into an `oauth2.Request` object. """
    headers = {}
    if 'HTTP_AUTHORIZATION' in request.META:
        headers['Authorization'] = request.META['HTTP_AUTHORIZATION']

    # This allows you to send through duplicates in the forms. Otherwise you
    # get an error with invalid signatures.
    out = {}
    for k in request.REQUEST.iterkeys():
        v = request.REQUEST.getlist(k)
        out[k] = request.REQUEST.get(k) if len(v) == 1 else v

    return oauth.Request.from_request(request.method,
                                      request.build_absolute_uri(request.path),
                                      headers, out)


def verify_oauth_request(request, oauth_request, consumer, token=None):
    """ Helper function to verify requests. """
    from piston.authentication.oauth.store import store

    # Check nonce
    if not store.check_nonce(request, oauth_request, oauth_request['oauth_nonce']):
        return False

    # Verify request
    try:
        oauth_server = oauth.Server()
        oauth_server.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())
        oauth_server.add_signature_method(oauth.SignatureMethod_PLAINTEXT())

        # Ensure the passed keys and secrets are ascii, or HMAC will complain.
        consumer = oauth.Consumer(consumer.key.encode('ascii', 'ignore'), consumer.secret.encode('ascii', 'ignore'))
        if token is not None:
            token = oauth.Token(token.key.encode('ascii', 'ignore'), token.secret.encode('ascii', 'ignore'))

        oauth_server.verify_request(oauth_request, consumer, token)
    except oauth.Error:
        return False

    return True


def require_params(oauth_request, parameters=[]):
    """ Ensures that the request contains all required parameters. """
    params = [
        'oauth_consumer_key',
        'oauth_nonce',
        'oauth_signature',
        'oauth_signature_method',
        'oauth_timestamp'
    ]
    params.extend(parameters)

    try:
        missing = list(param for param in params if param not in oauth_request)
    except:
        missing = params

    if missing:
        return HttpResponseBadRequest('Missing OAuth parameters: %s' % (', '.join(missing)))

    return None

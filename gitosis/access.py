import os, logging
from ConfigParser import NoSectionError, NoOptionError
from gitosis import group

import httplib
import simplejson as json 

def haveAccess(config, user, mode, path):
    """
    Map request for write access to allowed path.

    Note for read-only access, the caller should check for write
    access too.

    Returns ``None`` for no access, or a tuple of toplevel directory
    containing repositories and a relative path to the physical repository.

    expects to find the following in the gitosis config

    [rsp]
    haveAccessURL = www.example.org
    """

    access_url = config.get('rsp', 'haveAccessURL')
    if not access_url:
        raise Exception("uh... not configured with an haveAccessURL yet, add it under an [rsp] section")

    basename, ext = os.path.splitext(path)
    if ext == '.git':
        path = basename

    conn = httplib.HTTPConnection(access_url)
    conn.request("GET", "/hosts/%s/committers/%s" % (path, user))
    http_response = conn.getresponse()

    if http_response.status in range(200,300):
        # basically I'm lazy and didn't want to handle redirects
        # if that turns out to be a bad thing I'm sure I can write that
        # also, if rsp is down I just return false
        response = json.loads(http_response.read())
    else:
        return None

    if response['canCommit']:
        prefix = 'repositories'
        mapping = path
        return (prefix, mapping)
    else:
        return None

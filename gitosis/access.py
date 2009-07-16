import os, logging
import httplib
import simplejson as json

from ConfigParser import NoSectionError, NoOptionError

from gitosis import group

def haveAccess(config, user, mode, path):
    """
    Map request for write access to allowed path.

    Note for read-only access, the caller should check for write
    access too.

    Returns ``None`` for no access, or a tuple of toplevel directory
    containing repositories and a relative path to the physical repository.
    """

    access_url = config.get("rsp", "haveAccessURL")

    log = logging.getLogger('gitosis.access.haveAccess')

    log.debug(
        'Access check for %(user)r as %(mode)r on %(path)r...'
        % dict(user=user, mode=mode, path=path))


    basename, ext = os.path.splitext(path)
    if ext == '.git':
        log.debug(
            'Stripping .git suffix from %(path)r, new value %(basename)r'
            % dict( path=path, basename=basename,))

        path = basename

    response = check_with_rsp(access_url, user, mode, path)
    if response:
        return response

    groups = config.groups()
    
    for group in Group.member_of(user, groups):
        repos = group.modes[mode]

        mapping = None

        if path in repos:
            log.debug(
                'Access ok for %(user)r as %(mode)r on %(path)r'
                % dict( user=user, mode=mode, path=path,))
            mapping = path
        else:
            try:
                mapping = config.get('group %s' % groupname,
                                     'map %s %s' % (mode, path))
            except (NoSectionError, NoOptionError):
                pass
            else:
                log.debug(
                    'Access ok for %(user)r as %(mode)r on %(path)r=%(mapping)r'
                    % dict( user=user, mode=mode, path=path, mapping=mapping,))

        if mapping is not None:
            prefix = None
            try:
                prefix = config.get(
                    'group %s' % groupname, 'repositories')
            except (NoSectionError, NoOptionError):
                try:
                    prefix = config.get('gitosis', 'repositories')
                except (NoSectionError, NoOptionError):
                    prefix = 'repositories'

            log.debug(
                'Using prefix %(prefix)r for %(path)r'
                % dict( prefix=prefix, path=mapping,))
            return (prefix, mapping)

def check_with_rsp(access_url, user, mode, path):
    """
    expects to find the following in the gitosis config 
    [rsp]
    haveAccessURL = www.example.org
    """
#    if not access_url:
#        raise Exception("uh... not configured with an haveAccessURL yet, add it under an [rsp] section")

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

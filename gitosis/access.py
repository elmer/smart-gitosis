import os, logging
import httplib
import simplejson as json
import base64 as base64

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

    response = check_with_rsp(config, user, mode, path)
    if response:
        return response

    for groupname in group.getMembership(config=config, user=user):
        log.debug('trying: user %(user)r in group %(group)r' % dict(user=user, group=groupname))

        try:
            repos = config.get('group %s' % groupname, mode)
        except (NoSectionError, NoOptionError):
            repos = []
        else:
            repos = repos.split()

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

def check_with_rsp(config, user, mode, path):
    """
    expects to find the following in the gitosis config 
    [rsp]
    haveAccessURL = www.example.org
    """

    log = logging.getLogger('gitosis.access.check_with_rsp')

    if not config.has_section('rsp'):
        log.debug("No RSP section");
        return None

    access_url = config.get('rsp', 'haveAccessURL')
    username = None
    password = None
    try:
        username = config.get('rsp', 'acl_user')
        password = config.get('rsp', 'acl_pass')
    except:
        pass
    
    headers = dict() 
    if( username and password ):
        auth =  base64.encodestring(username + ':' + password).strip
        headers['Authorization'] = "Basic %s" % auth

    if not access_url:
        log.debug("No 'haveAccessURL' set");
        raise Exception("uh... not configured with an haveAccessURL yet, add it under an [rsp] section")

    basename, ext = os.path.splitext(path)
    if ext == '.git':
        path = basename

    conn = httplib.HTTPConnection(access_url)
    conn.request("GET", "/hosts/%s/committers/%s" % (path, user), None, headers)

    try:
        log.debug("Attempting to fetch from URL %(url)r" % dict( url=access_url ));
        http_response = conn.getresponse()
    except:
        log.debug("Unable to fetch data from haveAccessURL");
        return None

    log.debug("Got back reponse: %(code)r" % dict( code=http_response.status ));

    if http_response.status in range(200,300):
        # basically I'm lazy and didn't want to handle redirects
        # if that turns out to be a bad thing I'm sure I can write that
        # also, if rsp is down I just return false
        response = json.loads(http_response.read())
    else:
        return None

    if response['canCommit']:
        log.debug("User '%(user)r' can commit" % dict( user=user ));
        prefix = 'repositories'
        mapping = path
        return (prefix, mapping)
    else:
        log.debug("User '%(user)r' cannot commit" % dict( user=user ));
        return None

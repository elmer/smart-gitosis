from __future__ import with_statement 
import os, errno, re
import logging

log = logging.getLogger('gitosis.ssh')

_ACCEPTABLE_USER_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_.-]*(@[a-zA-Z][a-zA-Z0-9.-]*)?$')

def isSafeUsername(user):
    match = _ACCEPTABLE_USER_RE.match(user)
    return (match is not None)

def readKeys(keydir):
    """
    Read SSH public keys from ``keydir/*.pub``
    """
    for filename in os.listdir(keydir):
        basename, ext = os.path.splitext(filename)

        if filename.startswith('.') or ext != '.pub':
            continue

        if not isSafeUsername(basename):
            log.warn('Unsafe SSH username in keyfile: %r', filename)
            continue

        path = os.path.join(keydir, filename)
        with open(path) as f:
            for line in f:
                line = line.rstrip('\n')
                yield (basename, line)

COMMENT = '### autogenerated by gitosis, DO NOT EDIT'


_COMMAND_RE = re.compile('^command="PATH=/opt/local/bin (.*gitosis-serve) [^"]+",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty .*')

def generateAuthorizedKeys(keys):
    TEMPLATE=('command="PATH=/opt/local/bin gitosis-serve %(user)s",no-port-forwarding,'
              +'no-X11-forwarding,no-agent-forwarding,no-pty %(key)s')

    yield COMMENT
    for (user, key) in keys:
        yield TEMPLATE % dict(user=user, key=key)

def filterAuthorizedKeys(fp):
    """
    Read lines from ``fp``, filter out autogenerated ones.

    Note removes newlines.
    """

    for line in fp:
        line = line.rstrip('\n')
        if line == COMMENT:
            continue
        if _COMMAND_RE.match(line):
            continue
        yield line

def writeAuthorizedKeys(path, keydir):
    filtered_keys = []

    with open(path, 'r') as in_file:
        filtered_keys = [line for line in filterAuthorizedKeys(in_file)]

    keygen = readKeys(keydir)
    authorized_keys = [line for line in generateAuthorizedKeys(keygen)]

    with open(path, 'w') as out_file:
        out_file.write("\n".join(filtered_keys) + "\n")

        out_file.write("\n".join(authorized_keys))

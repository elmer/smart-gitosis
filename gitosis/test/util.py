from __future__ import with_statement 
from nose.tools import eq_ as eq

import errno
import os
import shutil
import stat
import sys

def mkdir(*a, **kw):
    try:
        os.mkdir(*a, **kw)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

def maketemp():
    tmp = os.path.join(os.path.dirname(__file__), 'tmp')
    mkdir(tmp)

    caller = sys._getframe(1)
    name = '%s.%s' % (
        sys._getframe(1).f_globals['__name__'],
        caller.f_code.co_name,
        )
    tmp = os.path.join(tmp, name)
    try:
        shutil.rmtree(tmp)
    except OSError, e:
        if e.errno == errno.ENOENT:
            pass
        else:
            raise
    os.mkdir(tmp)
    return tmp

def writeFile(path, content):
    with open(path, 'w') as f:
        f.write(content)

def readFile(path):
    with open(path, 'r') as f:
        return f.read()

def assert_raises(excClass, callableObj, *args, **kwargs):
    """
    Like unittest.TestCase.assertRaises, but returns the exception.
    """
    try:
        callableObj(*args, **kwargs)
    except excClass, e:
        return e
    else:
        if hasattr(excClass,'__name__'): excName = excClass.__name__
        else: excName = str(excClass)
        raise AssertionError("%s not raised" % excName)

def check_mode(path, mode, is_file=None, is_dir=None):
    st = os.stat(path)
    if is_dir:
        assert stat.S_ISDIR(st.st_mode)
    if is_file:
        assert stat.S_ISREG(st.st_mode)

    got = stat.S_IMODE(st.st_mode)
    eq(got, mode, 'File mode %04o!=%04o for %s' % (got, mode, path))

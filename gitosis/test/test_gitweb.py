from nose.tools import eq_ as eq

import os
from ConfigParser import RawConfigParser
from cStringIO import StringIO

from gitosis import gitweb
from gitosis.test.util import mkdir, maketemp, readFile, writeFile

def test_projectsList_empty():
    cfg = RawConfigParser()
    eq(gitweb.generate_project_list(cfg), [])

def test_projectsList_repoDenied():
    cfg = RawConfigParser()
    cfg.add_section('repo foo/bar')
    eq(gitweb.generate_project_list(cfg), [])

def test_projectsList_noOwner():
    """
    This is a failing test because the repository
    directories do not exist. I'm not sure it
    ever made any sense
    """

    cfg = RawConfigParser()
    cfg.add_section('repo foo/bar')
    cfg.set('repo foo/bar', 'gitweb', 'yes')
    #eq(gitweb.generate_project_list(cfg), ['foo%2Fbar'])
    eq(gitweb.generate_project_list(cfg), [])

def test_projectsList_haveOwner():
    """
    This is a failing test because the repository
    directories do not exist. I'm not sure it
    ever made any sense
    """

    cfg = RawConfigParser()
    cfg.add_section('repo foo/bar')
    cfg.set('repo foo/bar', 'gitweb', 'yes')
    cfg.set('repo foo/bar', 'owner', 'John Doe')
    #eq(gitweb.generate_project_list(cfg), ['foo%2Fbar John+Doe'])
    eq(gitweb.generate_project_list(cfg), [])

def test_projectsList_multiple():
    """
    This is a failing test because the repository
    directories do not exist. I'm not sure it
    ever made any sense
    """

    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.add_section('repo foo/bar')
    cfg.set('repo foo/bar', 'owner', 'John Doe')
    cfg.set('repo foo/bar', 'gitweb', 'yes')
    cfg.add_section('repo quux')
    cfg.set('repo quux', 'gitweb', 'yes')
    #eq(gitweb.generate_project_list(cfg), ['quux', 'foo%2Fbar John+Doe'])
    eq(gitweb.generate_project_list(cfg), [])

def test_projectsList_multiple_globalGitwebYes():
    """
    This is a failing test because the repository
    directories do not exist. I'm not sure it
    ever made any sense
    """
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'gitweb', 'yes')
    cfg.add_section('repo foo/bar')
    cfg.set('repo foo/bar', 'owner', 'John Doe')
    cfg.add_section('repo quux')
    # same as default, no effect
    cfg.set('repo quux', 'gitweb', 'yes')
    cfg.add_section('repo thud')
    # this is still hidden
    cfg.set('repo thud', 'gitweb', 'no')
    #eq(gitweb.generate_project_list(cfg), ['quux', 'foo%2Fbar John+Doe'])
    eq(gitweb.generate_project_list(cfg), [])

def test_projectsList_reallyEndsWithGit():
    tmp = maketemp()
    path = os.path.join(tmp, 'foo.git')
    mkdir(path)
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'gitweb', 'yes')
    eq(gitweb.generate_project_list(cfg), ['foo.git'])

def test_projectsList_path():
    tmp = maketemp()
    path = os.path.join(tmp, 'foo.git')
    mkdir(path)
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'gitweb', 'yes')
    projects_list = os.path.join(tmp, 'projects.list')
    gitweb.write_project_list(cfg, projects_list)
    got = readFile(projects_list)
    eq(got, 'foo.git')

def test_description_none():
    tmp = maketemp()
    path = os.path.join(tmp, 'foo.git')
    mkdir(path)
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'description', 'foodesc')
    gitweb.set_descriptions(
        config=cfg,
        )
    got = readFile(os.path.join(path, 'description'))
    eq(got, 'foodesc\n')

def test_description_repo_missing():
    # configured but not created yet; before first push
    tmp = maketemp()
    path = os.path.join(tmp, 'foo.git')
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'description', 'foodesc')
    gitweb.set_descriptions(
        config=cfg,
        )
    assert not os.path.exists(os.path.join(tmp, 'foo'))
    assert not os.path.exists(os.path.join(tmp, 'foo.git'))

def test_description_repo_missing_parent():
    # configured but not created yet; before first push
    tmp = maketemp()
    path = os.path.join(tmp, 'foo/bar.git')
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'description', 'foodesc')
    gitweb.set_descriptions(
        config=cfg,
        )
    assert not os.path.exists(os.path.join(tmp, 'foo'))

def test_description_default():
    tmp = maketemp()
    path = os.path.join(tmp, 'foo.git')
    mkdir(path)
    writeFile(
        os.path.join(path, 'description'),
        'Unnamed repository; edit this file to name it for gitweb.\n',
        )
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'description', 'foodesc')
    gitweb.set_descriptions(
        config=cfg,
        )
    got = readFile(os.path.join(path, 'description'))
    eq(got, 'foodesc\n')

def test_description_not_set():
    tmp = maketemp()
    path = os.path.join(tmp, 'foo.git')
    mkdir(path)
    writeFile(
        os.path.join(path, 'description'),
        'i was here first\n',
        )
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('repo foo')
    gitweb.set_descriptions(
        config=cfg,
        )
    got = readFile(os.path.join(path, 'description'))
    eq(got, 'i was here first\n')

def test_description_again():
    tmp = maketemp()
    path = os.path.join(tmp, 'foo.git')
    mkdir(path)
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'description', 'foodesc')
    gitweb.set_descriptions(
        config=cfg,
        )
    gitweb.set_descriptions(
        config=cfg,
        )
    got = readFile(os.path.join(path, 'description'))
    eq(got, 'foodesc\n')

from nose.tools import eq_ as eq
from gitosis.test.util import assert_raises

import logging
import os
from os import path
from cStringIO import StringIO
from ConfigParser import RawConfigParser

from gitosis import serve
from gitosis import repository

from gitosis.test import util

def test_bad_newLine():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.CommandMayNotContainNewlineError,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command='ev\nil',
        )
    eq(str(e), 'Command may not contain newline')
    assert isinstance(e, serve.ServingError)

def test_bad_dash_noargs():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.UnknownCommandError,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command='git-upload-pack',
        )
    eq(str(e), 'Unknown command denied')
    assert isinstance(e, serve.ServingError)

def test_bad_space_noargs():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.UnknownCommandError,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command='git upload-pack',
        )
    eq(str(e), 'Unknown command denied')
    assert isinstance(e, serve.ServingError)

def test_bad_command():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.UnknownCommandError,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="evil 'foo'",
        )
    eq(str(e), 'Unknown command denied')
    assert isinstance(e, serve.ServingError)

def test_bad_unsafeArguments_notQuoted():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.UnsafeArgumentsError,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git-upload-pack foo",
        )
    eq(str(e), 'Arguments to command look dangerous')
    assert isinstance(e, serve.ServingError)

def test_bad_unsafeArguments_badCharacters():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.UnsafeArgumentsError,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git-upload-pack 'ev!l'",
        )
    eq(str(e), 'Arguments to command look dangerous')
    assert isinstance(e, serve.ServingError)

def test_bad_unsafeArguments_dotdot():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.UnsafeArgumentsError,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git-upload-pack 'something/../evil'",
        )
    eq(str(e), 'Arguments to command look dangerous')
    assert isinstance(e, serve.ServingError)

def test_bad_forbiddenCommand_read_dash():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.ReadAccessDenied,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git-upload-pack 'foo'",
        )
    eq(str(e), 'Repository read access denied')
    assert isinstance(e, serve.AccessDenied)
    assert isinstance(e, serve.ServingError)

def test_bad_forbiddenCommand_read_space():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.ReadAccessDenied,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git upload-pack 'foo'",
        )
    eq(str(e), 'Repository read access denied')
    assert isinstance(e, serve.AccessDenied)
    assert isinstance(e, serve.ServingError)

def test_bad_forbiddenCommand_write_noAccess_dash():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.ReadAccessDenied,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo'",
        )
    # error message talks about read in an effort to make it more
    # obvious that jdoe doesn't have *even* read access
    eq(str(e), 'Repository read access denied')
    assert isinstance(e, serve.AccessDenied)
    assert isinstance(e, serve.ServingError)

def test_bad_forbiddenCommand_write_noAccess_space():
    cfg = RawConfigParser()
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.ReadAccessDenied,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git receive-pack 'foo'",
        )
    # error message talks about read in an effort to make it more
    # obvious that jdoe doesn't have *even* read access
    eq(str(e), 'Repository read access denied')
    assert isinstance(e, serve.AccessDenied)
    assert isinstance(e, serve.ServingError)

def test_bad_forbiddenCommand_write_readAccess_dash():
    cfg = RawConfigParser()
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'readonly', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.WriteAccessDenied,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo'",
        )
    eq(str(e), 'Repository write access denied')
    assert isinstance(e, serve.AccessDenied)
    assert isinstance(e, serve.ServingError)

def test_bad_forbiddenCommand_write_readAccess_space():
    cfg = RawConfigParser()
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'readonly', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    e = assert_raises(
        serve.WriteAccessDenied,
        serve.serve,
        cfg=cfg,
        user='jdoe',
        command="git receive-pack 'foo'",
        )
    eq(str(e), 'Repository write access denied')
    assert isinstance(e, serve.AccessDenied)
    assert isinstance(e, serve.ServingError)

def test_simple_read_dash():
    tmp = util.maketemp()
    repository.init(path.join(tmp, 'foo.git'))
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'readonly', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    got = serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-upload-pack 'foo'",
        )
    eq(got, "git-upload-pack '%s/foo.git'" % tmp)

def test_simple_read_space():
    tmp = util.maketemp()
    repository.init(path.join(tmp, 'foo.git'))
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'readonly', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    got = serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git upload-pack 'foo'",
        )
    eq(got, "git upload-pack '%s/foo.git'" % tmp)

def test_simple_write_dash():
    tmp = util.maketemp()
    repository.init(path.join(tmp, 'foo.git'))
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    got = serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo'",
        )
    eq(got, "git-receive-pack '%s/foo.git'" % tmp)

def test_simple_write_space():
    tmp = util.maketemp()
    repository.init(path.join(tmp, 'foo.git'))
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    got = serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git receive-pack 'foo'",
        )
    eq(got, "git receive-pack '%s/foo.git'" % tmp)

def test_push_inits_if_needed():
    # a push to a non-existent repository (but where config authorizes
    # you to do that) will create the repository on the fly
    tmp = util.maketemp()

    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)

    generated = path.join(tmp, 'generated')
    os.mkdir(generated)

    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', repositories)
    cfg.set('gitosis', 'generate-files-in', generated)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')

    serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo'",
        )

    eq(os.listdir(repositories), ['foo.git'])
    assert path.isfile(path.join(repositories, 'foo.git', 'HEAD'))

def test_push_inits_if_needed_haveExtension():
    # a push to a non-existent repository (but where config authorizes
    # you to do that) will create the repository on the fly
    tmp = util.maketemp()
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)
    cfg.set('gitosis', 'repositories', repositories)
    generated = path.join(tmp, 'generated')
    os.mkdir(generated)
    cfg.set('gitosis', 'generate-files-in', generated)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo.git'",
        )
    eq(os.listdir(repositories), ['foo.git'])
    assert path.isfile(path.join(repositories, 'foo.git', 'HEAD'))

def test_push_inits_subdir_parent_missing():
    tmp = util.maketemp()
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)
    cfg.set('gitosis', 'repositories', repositories)
    generated = path.join(tmp, 'generated')
    os.mkdir(generated)
    cfg.set('gitosis', 'generate-files-in', generated)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo/bar')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo/bar.git'",
        )
    eq(os.listdir(repositories), ['foo'])
    foo = path.join(repositories, 'foo')
    util.check_mode(foo, 0750, is_dir=True)
    eq(os.listdir(foo), ['bar.git'])
    assert path.isfile(path.join(repositories, 'foo', 'bar.git', 'HEAD'))

def test_push_inits_subdir_parent_exists():
    tmp = util.maketemp()
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)
    foo = path.join(repositories, 'foo')
    # silly mode on purpose; not to be touched
    os.mkdir(foo, 0751)
    cfg.set('gitosis', 'repositories', repositories)
    generated = path.join(tmp, 'generated')
    os.mkdir(generated)
    cfg.set('gitosis', 'generate-files-in', generated)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo/bar')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo/bar.git'",
        )
    eq(os.listdir(repositories), ['foo'])
    util.check_mode(foo, 0751, is_dir=True)
    eq(os.listdir(foo), ['bar.git'])
    assert path.isfile(path.join(repositories, 'foo', 'bar.git', 'HEAD'))

def test_push_inits_if_needed_existsWithExtension():
    tmp = util.maketemp()
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)
    cfg.set('gitosis', 'repositories', repositories)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')
    os.mkdir(path.join(repositories, 'foo.git'))
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo'",
        )
    eq(os.listdir(repositories), ['foo.git'])
    # it should *not* have HEAD here as we just mkdirred it and didn't
    # create it properly, and the mock repo didn't have anything in
    # it.. having HEAD implies serve ran git init, which is supposed
    # to be unnecessary here
    eq(os.listdir(path.join(repositories, 'foo.git')), [])

def test_push_inits_no_stdout_spam():
    # git init has a tendency to spew to stdout, and that confuses
    # e.g. a git push
    tmp = util.maketemp()
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)
    cfg.set('gitosis', 'repositories', repositories)
    generated = path.join(tmp, 'generated')
    os.mkdir(generated)
    cfg.set('gitosis', 'generate-files-in', generated)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    old_stdout = os.dup(1)
    try:
        new_stdout = os.tmpfile()
        os.dup2(new_stdout.fileno(), 1)
        serve.serve(
            cfg=cfg,
            user='jdoe',
            command="git-receive-pack 'foo'",
            )
    finally:
        os.dup2(old_stdout, 1)
        os.close(old_stdout)
    new_stdout.seek(0)
    got = new_stdout.read()
    new_stdout.close()
    eq(got, '')
    eq(os.listdir(repositories), ['foo.git'])
    assert path.isfile(path.join(repositories, 'foo.git', 'HEAD'))

def test_push_inits_sets_description():
    tmp = util.maketemp()
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)
    cfg.set('gitosis', 'repositories', repositories)
    generated = path.join(tmp, 'generated')
    os.mkdir(generated)
    cfg.set('gitosis', 'generate-files-in', generated)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'description', 'foodesc')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo'",
        )
    eq(os.listdir(repositories), ['foo.git'])
    description = path.join(repositories, 'foo.git', 'description')
    assert path.exists(description)
    got = util.readFile(description)
    eq(got, 'foodesc')

def test_push_inits_updates_projects_list():
    tmp = util.maketemp()

    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)

    generated = path.join(tmp, 'generated')
    os.mkdir(generated)

    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', repositories)
    cfg.set('gitosis', 'generate-files-in', generated)

    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')

    cfg.add_section('repo foo')
    cfg.set('repo foo', 'gitweb', 'yes')

    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')

    os.mkdir(path.join(repositories, 'gitosis-admin.git'))

    serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo'",
        )

    eq(
        sorted(os.listdir(repositories)),
        sorted(['foo.git', 'gitosis-admin.git']),
        )

    project_list = path.join(generated, 'projects.list')

    assert path.exists(project_list)

    eq(util.readFile(project_list), 'foo.git')

def test_push_inits_sets_export_ok():
    tmp = util.maketemp()
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    repositories = path.join(tmp, 'repositories')
    os.mkdir(repositories)
    cfg.set('gitosis', 'repositories', repositories)
    generated = path.join(tmp, 'generated')
    os.mkdir(generated)
    cfg.set('gitosis', 'generate-files-in', generated)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writable', 'foo')
    cfg.add_section('repo foo')
    cfg.set('repo foo', 'daemon', 'yes')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-receive-pack 'foo'",
        )
    eq(os.listdir(repositories), ['foo.git'])
    export = path.join(repositories, 'foo.git', 'git-daemon-export-ok')
    assert path.exists(export)

def test_absolute():
    # as the only convenient way to use non-standard SSH ports with
    # git is via the ssh://user@host:port/path syntax, and that syntax
    # forces absolute urls, just force convert absolute paths to
    # relative paths; you'll never really want absolute paths via
    # gitosis, anyway.
    tmp = util.maketemp()
    repository.init(path.join(tmp, 'foo.git'))
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'readonly', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    got = serve.serve(
        cfg=cfg,
        user='jdoe',
        command="git-upload-pack '/foo'",
        )
    eq(got, "git-upload-pack '%s/foo.git'" % tmp)

def test_typo_writeable():
    tmp = util.maketemp()
    repository.init(path.join(tmp, 'foo.git'))
    cfg = RawConfigParser()
    cfg.add_section('gitosis')
    cfg.set('gitosis', 'repositories', tmp)
    cfg.add_section('group foo')
    cfg.set('group foo', 'members', 'jdoe')
    cfg.set('group foo', 'writeable', 'foo')
    cfg.add_section('rsp')
    cfg.set('rsp', 'haveAccessURL', 'example.org')
    log = logging.getLogger('gitosis.serve')
    buf = StringIO()
    handler = logging.StreamHandler(buf)
    log.addHandler(handler)
    try:
        got = serve.serve(
            cfg=cfg,
            user='jdoe',
            command="git-receive-pack 'foo'",
            )
    finally:
        log.removeHandler(handler)
    eq(got, "git-receive-pack '%s/foo.git'" % tmp)
    handler.flush()
    eq(
        buf.getvalue(),
        "Repository 'foo' config has typo \"writeable\", shou"
        +"ld be \"writable\"\n",
        )

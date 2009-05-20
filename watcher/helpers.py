from os import path, mkdir, devnull, chdir
from subprocess import Popen

from hashlib import md5
from uuid import uuid1

def uuid():
    """
    generates a uuid, removes "-"'s
    """
    return str(uuid1()).replace('-', '')

def random_string(salt = "JoyentSalt"):
    m = md5()
    m.update(uuid())
    m.update(salt)
    return m.hexdigest()

def random_queue():
    return "smart+%s" % (random_string())

def update_or_create_repository(repository, projects_dir, git_user="git",
                                git_server="localhost"):
    project_path = path.join(projects_dir, repository[:-4])
    
    if path.exists(project_path):
        chdir(project_path)
        cmd = ["git", "pull"]
    else:
        clone_uri = "%s@%s:%s" % (git_user, git_server, repository)
        cmd = ["git", "clone", clone_uri, project_path]
    return call(cmd)

def process_config(config):
    return {
     'host': config.get('amqp', 'host'),
     'port': int(config.get('amqp', 'port')),
     'user_id': config.get('amqp', 'user_id'),
     'password': config.get('amqp', 'password'),
     'projects_dir': config.get('rsp', 'projects_dir'),
     'git_user': config.get('rsp', 'git_user'),
     'git_server': config.get('rsp', 'git_server'),
     'exchange': config.get('amqp', 'exchange'),
    }

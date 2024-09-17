#!/usr/bin/env python
import os
import git
from datetime import date
from src.osw_incline.version import __version__

project_path = os.path.dirname(os.path.abspath(__file__))
version_file_path = '{}/version.py'.format(project_path)

repo = git.Repo(search_parent_directories=True)
sha = repo.head.object.hexsha

build_date = date.today().strftime('%Y-%m-%d')

version = __version__

with open(version_file_path, 'w+') as version_file:
    version_file.write("version = '{}'\n".format(version))
    version_file.write("lastCommit = '{}'\n".format(sha))
    version_file.write("lastCommitShort = '{}'\n".format(
        repo.git.rev_parse(sha, short=1)))
    version_file.write("buildDate = '{}'\n".format(build_date))
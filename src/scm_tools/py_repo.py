#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for Python Package Repository
"""
import os
import json
import getpass
from collections import OrderedDict

from logIO import get_logger
from my_python import constants
from my_python.system.file_manager import remove_from_disk


# sibling imports
import git_utils
import constants as scm_constants

logger = get_logger(__name__)


class PackageBuilder(object):
    """
    class docs
    """
    def __init__(self, name, root_path=None):
        self.name = name
        _root_path = root_path if root_path else os.getcwd()
        self.root_path = get_project_root_from_path(source_path=_root_path)
        if not self.root_path:
            logger.error("Path '{0}' is not a valid project.".format(_root_path), exc_info=True)

    def install_to_disk(self, output_path, symlink=False):
        pass

    def remove_from_disk(self, from_symlink=True):
        pass

    def get_latest_build_version(self):
        pass

    def next_version(self):
        pass

    def add_dependency(self, package_name):
        pass

    @property
    def is_source_package(self):
        return constants.PY_SOURCE_DIR in self.root_path

    @property
    def is_build_package(self):
        return constants.PY_BUILDS_DIR in self.root_path

    @property
    def is_testing_package(self):
        return constants.PY_TESTING_DIR in self.root_path

    def get_requirements_file(self):
        """
        Get the requirements file if any for the project, Returns None if nothing.

        :return             `str`           Requirements file path if found else None
        """
        req_file = os.path.join(self.root_path, constants.requirements_file)
        if os.path.isfile(req_file):
            return req_file
        logger.warning("Cannot find requirements file for '{0}' project.".format(self.name))
        return None

    def get_package_setup_file(self):
        """
        Get the package_setup file if any for the project, Returns None if nothing.

        :return             `str`           package_setup file path if found else None
        """
        setup_file = os.path.join(self.root_path, constants.package_setup_file)
        if os.path.isfile(setup_file):
            return setup_file
        logger.error("Cannot find package_setup file for '{0}' project.".format(self.name))
        return None


class PythonPackage(object):
    """
    Main class to call


    package = PythonPackage()

    package.isValid()
    package.build(for_test=True)
    package.remove()

    package.rebase(with_branch)
    package.push(create_pr)
    package.develop()

    package.get_paths(version)

    """
    def __init__(self, name, root_path):
        self.name = name
        self.root_path = root_path



def get_project_root_from_path(source_path):
    """
    Generic method to get the project root path from given path. The func can be really handy
    for all the projects as you can get the project root directory from a given path

    i.e.
        Lets assume you have a path where your files are there

        /local/scm_tools/src/
                            /scm_tools
                                /__init__.py
                                /common.py


        Now you'd want to know the root directory of project for many reason such as get the
        package_setup.py file, read the requirement.txt file etc.

        With this method you can pass any of following paths and It will return you the PyProject object which
        contains lots of useful attributes.

    :param source_path:         `str`                       AbsPath for the project
    :return:                    `PyProjectInstance`         PyProject Instance for given path of found else None
    """
    def _get_root_directory(src_path, path_checked=None):
        path_checked = list() if path_checked is None else path_checked
        if src_path is None or not os.path.exists(src_path):
            return None

        if src_path in path_checked:
            # It's repeating this path, If this path was root directory, The function would have returned the
            # path so no need to waste checking it again.
            return None

        if os.path.isfile(src_path):
            src_path = os.path.dirname(src_path)

        if constants.package_setup_file in os.listdir(src_path):
            return src_path

        path_checked.append(src_path)
        return _get_root_directory(src_path=os.path.dirname(src_path), path_checked=path_checked)

    root_path = _get_root_directory(src_path=source_path)
    if root_path is None:
        logger.warning("Given path is not a valid project.")
        return None

    return root_path


class VersionController(object):
    """
    class docs
    """
    def __init__(self, pkg_name, ssh_path=None, ticket_id=None, ticket_url=None, disk_path=None):
        super(VersionController, self).__init__()
        self.pkg_name = pkg_name
        self.description = None

        self.ssh_path = ssh_path or git_utils.get_ssh_path_for_repo(repository_name=self.pkg_name)
        self.ticket_id = ticket_id
        self.ticket_url = ticket_url or git_utils.get_ticket_url_from_id(ticket_id=self.ticket_id)

        self.disk_path = disk_path or os.path.join(os.getcwd(), self.pkg_name)

    def _write_config(self):
        self.cd_to_directory()

        data_dict = OrderedDict()
        data_dict["pkg_name"] = self.pkg_name
        data_dict["ssh_path"] = self.ssh_path
        data_dict["ticket_id"] = self.ticket_id
        data_dict["ticket_url"] = self.ticket_url
        data_dict["disk_path"] = self.disk_path
        data_dict["user"] = getpass.getuser()

        with open(scm_constants.PACKAGE_CONFIG_FILE, "w") as write_cfg:
            json.dump(data_dict, write_cfg, indent=4)

    @staticmethod
    def _read_config(directory_path):
        file_path = os.path.join(directory_path, scm_constants.PACKAGE_CONFIG_FILE)
        if not os.path.isfile(file_path):
            return {}

        with open(file_path, "r") as read_cfg:
            return json.load(read_cfg)

    @classmethod
    def from_path(cls, path=None):
        """
        From given path or os.getcwd(), get the class object
        """
        path = path or os.getcwd()
        read_config = cls._read_config(directory_path=path)
        if read_config:
            # It has the scmconfig file, we can just read this and get the project info
            read_config.pop("user")
            return cls(**read_config)

        from my_python.common.general import get_project_root_from_path
        project = get_project_root_from_path(source_path=path)
        if not project:
            logger.warning("This is not an valid project path. '{0}'".format(path))
            return False

        read_config = cls._read_config(directory_path=project.root_path)
        if read_config:
            read_config.pop("user")
            return cls(**read_config)

        # this means It's a valid project but It doesn't have
        # the scmconfig file in it.
        obj = cls(pkg_name=project.name, disk_path=project.root_path)
        obj._write_config()
        return obj

    def __repr__(self):
        return "ClassObject : {cls}:{name}:{branch} - {desc}".format(cls=self.__class__.__name__,
                                                                     name=self.pkg_name,
                                                                     branch=self.active_branch,
                                                                     desc=self.description)

    @property
    def active_branch(self):
        """
        Return the active branch name, None if not a valid git repo
        """
        return git_utils.get_git_active_branch(directory_path=self.disk_path)

    def get_active_branch(self):
        return self.active_branch

    def get_ssh_path(self):
        return self.ssh_path

    def cd_to_directory(self, to_path=None):
        to_path = to_path or self.disk_path
        os.chdir(to_path)

    def init_development(self, source_branch=None, to_branch=None, description=None, overwrite_existing=True):
        """
        This should be run to initialize the development branch
        """
        clone_repo = self.clone(source_branch=source_branch, overwrite_existing=overwrite_existing)
        if not clone_repo:
            return False

        self.cd_to_directory()
        self.develop(to_branch=to_branch, source_branch=source_branch, description=description, need_rebase=False)
        self.install(force=overwrite_existing)
        return True

    def _add_to_package_group(self):
        raise NotImplementedError

    def clone(self, source_branch=None, overwrite_existing=None):
        """
        Method for cloning the repository
        """
        current_dir = os.getcwd()

        if self.pkg_name in os.listdir(current_dir):
            if overwrite_existing:
                remove_from_disk(path=os.path.join(current_dir, self.pkg_name))
            else:
                logger.error("Package already exists, Please use force/override flags to force clone.")
                return False

        if self.ssh_path:
            success = git_utils.clone_repository(git_ssh_url=self.ssh_path, branch=source_branch)
            if success:
                return self._write_config()

        return False

    def rebase(self, with_branch=None):
        """
        Method for rebasing your current branch with latest origin-master branch
        """
        return git_utils.do_git_rebase(source_branch=with_branch)

    def push(self, to_branch=None, open_merge_request=True, force=False):
        """
        Method for pushing your changes to $to_branch and create merge_request if asked by user
        """
        self.rebase()
        return git_utils.do_git_push(to_branch=to_branch, pull_request=open_merge_request, force=force)

    def install(self, to_path=None, hard_link=False, force=True):
        """
        Method to install your repo to a certain path. This can be used when developer wants to give
        his code base for testing.
        """
        raise NotImplementedError

    def develop(self, to_branch, source_branch=None, description=None, need_rebase=True):
        """
        Main start-development method

            *   self.rebase() if user asked
            *   checkout $source_branch
            *   create a new branch called $to_branch
        """
        if need_rebase:
            self.rebase(with_branch=source_branch)

        git_utils.create_dev_branch(dev_branch=to_branch, source_branch=source_branch, description=description)

    @property
    def package(self):
        return self



if __name__ == "__main__":
    x = BasePythonPackage(name="Asd", )

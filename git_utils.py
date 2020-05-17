# -*- coding: utf-8 -*-
"""
Main module which contains all the git methodology
"""
import os
import json
import getpass
import traceback
import subprocess
from collections import OrderedDict

from logIO import get_logger
from . import constants as scm_constants
from my_python.decorators.context_decorators import RunFromPath
from my_python.system.file_manager import remove_from_disk

logger = get_logger(__name__)


def get_ssh_path_for_repo(repository_name):
    """
    Get the repository

    :param repository_name:         `str`           project/repository name
    :return:                        `str`           git ssh path for the repository
    """
    # TODO check if the repository path is valid.
    return scm_constants.BASE_URL.format(repository_name)


def get_ticket_url_from_id(ticket_id):
    """
    Get the associate ticket id

    :param ticket_id:         `str`           ticket_id
    :return:                  `str`           ticket url
    """
    return "https://jira.com/id={0}".format(ticket_id)


def clone_repository(git_ssh_url, branch=None, directory_path=None):
    """
    Clone the given git_ssh_url to given directory_path
    """
    directory_path = directory_path or os.getcwd()

    with RunFromPath(path=directory_path):
        command_string = "git clone {0}".format(git_ssh_url)
        if branch:
            command_string += " -b {0}".format(branch)
        logger.info("Running: '{0}' ".format(command_string))
        os.system(command_string)

    return True


def get_all_git_branches(directory_path=None):
    """
    get all the git branches from given directory_path or os.getcwd()
    :param directory_path:
    :return:
    """
    directory_path = directory_path or os.getcwd()

    with RunFromPath(path=directory_path):
        try:
            data = subprocess.check_output(["git", "branch"])
            return [x.strip() for x in data.split("\n") if x]

        except subprocess.CalledProcessError:
            return list()

        except Exception, e:
            traceback.print_exc()
            logger.warning("Error while looking for git_active_branch at '{0}' : {1}".format(os.getcwd(), e))
            return list()


def get_git_active_branch(directory_path=None):
    """
    Get the active branch from directory_path or os.getcwd()
    """
    directory_path = directory_path or os.getcwd()

    with RunFromPath(path=directory_path):
        all_branches = get_all_git_branches()
        if not all_branches:
            return None

        all_valid_branches = [x for x in all_branches if scm_constants.ACTIVE_BRANCH_MARK in str(x)]
        if len(all_valid_branches) > 1:
            msg = "Something is wrong with your git repository.! Multiple branches are marked as active branch.!\n"
            msg += "Please go to '{0}' and run 'git branch' and find out more.!".format(os.getcwd())
            logger.error(msg)
            return None

        return str(all_valid_branches[0]).split(scm_constants.ACTIVE_BRANCH_MARK)[-1]


def do_git_rebase(source_branch=None, directory_path=None):
    """
    Do the rebase for active branch

    :param source_branch:       `str`           From which branch do you wants to do the rebase, defaults 'master'
    :param directory_path:      `str`           directory path of the project
    """
    directory_path = directory_path or os.getcwd()
    source_branch = source_branch or scm_constants.MASTER_BRANCH

    with RunFromPath(path=directory_path):
        active_branch = get_git_active_branch()

        if active_branch is not source_branch:
            logger.debug("You're not in the '{0}' branch. Switching back the branch to '{0}'".format(source_branch))
            try:
                os.system("git checkout {0}".format(source_branch))
            except subprocess.CalledProcessError:
                logger.warning("You have uncommitted changes in your local.!")
                logger.warning("Please commit your changes or stash them before you can switch branches.!")
                return False

        logger.debug("Fetching the data from upstream origin...")
        os.system("git fetch origin")

        logger.debug("Updating the local repo with origin/latest")
        os.system("git pull origin {0}".format(source_branch))

        logger.debug("Checkout the original branch.")
        os.system("git checkout {0}".format(active_branch))

        logger.debug("Running git rebase")
        os.system("git rebase {0}".format(source_branch))


def do_git_push(to_branch=None, pull_request=False, force=False):
    """
    Do the git push

    :param to_branch:           `str`
    :param pull_request:        `bool`
    :param force:               `bool`
    """
    to_branch = get_git_active_branch() if to_branch is None else to_branch
    directory_path = os.getcwd()

    with RunFromPath(path=directory_path):
        logger.debug("Pushing the changes to upstream")
        cmd = "git push origin {0}".format(to_branch)
        if force:
            cmd += " --force"
        os.system(cmd)


def create_dev_branch(dev_branch, source_branch=None, directory_path=None, description=None):
    """
    Create the Development branch
    """
    directory_path = directory_path or os.getcwd()
    source_branch = source_branch or scm_constants.MASTER_BRANCH

    with RunFromPath(path=directory_path):
        all_branches = get_git_active_branch()
        if not all_branches:
            return False

        if dev_branch in all_branches:
            logger.warning("{0} branch already exists in your local.".format(dev_branch))
            logger.warning("Run 'git pull origin {0}' to update your local branch with remote branch.!".format(dev_branch))
            return False

        active_branch = get_git_active_branch()
        if active_branch is not source_branch:
            logger.debug("You're not in the '{0}' branch. Switching back the branch to '{0}'".format(source_branch))
            try:
                os.system("git checkout {0}".format(source_branch))
            except subprocess.CalledProcessError:
                logger.warning("You have uncommitted changes in your local.!")
                logger.warning("Please commit your changes or stash them before you can switch branches.!")
                return False

        logger.debug("Fetching the data from upstream origin...")
        os.system("git fetch origin")

        logger.debug("Updating the local repo with origin/latest")
        os.system("git pull origin {0}".format(source_branch))

        logger.debug("Creating new branch.!")
        os.system("git checkout -b {0}".format(dev_branch))

        logger.debug("Setting up the upstream pointers...")
        os.system("git branch --set-upstream-to origin/{0}".format(source_branch))

        logger.info("Development branch created.!")
        return True


class PyGitRepository(object):
    """
    Python Git Repo

    Intended Usages:

    """
    def __init__(self, pkg_name, ssh_path=None, ticket_id=None, ticket_url=None, disk_path=None):
        super(PyGitRepository, self).__init__()
        self.pkg_name = pkg_name
        self.description = None

        self.ssh_path = ssh_path or get_ssh_path_for_repo(repository_name=self.pkg_name)
        self.ticket_id = ticket_id
        self.ticket_url = ticket_url or get_ticket_url_from_id(ticket_id=self.ticket_id)

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
        return "ClassObject : {cls}:{name}:{branch} - {desc}".format(cls=self.__class__.__name__, name=self.pkg_name,
                                                                     branch=self.active_branch, desc=self.description)

    @property
    def active_branch(self):
        """
        Return the active branch name, None if not a valid git repo
        """
        return get_git_active_branch(directory_path=self.disk_path)

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
            success = clone_repository(git_ssh_url=self.ssh_path, branch=source_branch)
            if success:
                return self._write_config()

        return False

    def rebase(self, with_branch=None):
        """
        Method for rebasing your current branch with latest origin-master branch
        """
        return do_git_rebase(source_branch=with_branch)

    def push(self, to_branch=None, open_merge_request=True, force=False):
        """
        Method for pushing your changes to $to_branch and create merge_request if asked by user
        """
        self.rebase()
        return do_git_push(to_branch=to_branch, pull_request=open_merge_request, force=force)

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

        create_dev_branch(dev_branch=to_branch, source_branch=source_branch, description=description)

    @property
    def package(self):
        return self

    @property
    def package_group(self):
        raise NotImplementedError


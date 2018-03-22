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
import constants as scm_constants
from my_python.decorators.context_decorators import RunFromPath

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



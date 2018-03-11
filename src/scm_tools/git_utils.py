# -*- coding: utf-8 -*-
"""
Main module which contains all the git methodology
"""

import os
import traceback
import subprocess

from . import constants as scm_constants
from my_python.decorators.context_decorators import RunFromPath


def clone_repository(git_ssh_url, branch=None, directory_path=None):
    """
    Clone the given git_ssh_url to given directory_path
    """
    directory_path = directory_path or os.getcwd()

    with RunFromPath(path=directory_path):
        command_string = "git clone {0}".format(git_ssh_url)
        if branch:
            command_string += " -b {0}".format(branch)
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
            print "Error while looking for git_active_branch at '{0}' : {1}".format(os.getcwd(), e)
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
            print msg
            return None

        return str(all_valid_branches[0]).split(scm_constants.ACTIVE_BRANCH_MARK)[-1]


def create_dev_branch(dev_branch, source_branch=None, directory_path=None, description=None):
    """
    Create the Development branch
    """
    directory_path = directory_path or os.getcwd()
    source_branch = source_branch or scm_constants.MASTER_BRANCH

    with RunFromPath(path=directory_path):

        all_branches = get_git_active_branch()
        if not all_branches:
            return

        if dev_branch in all_branches:
            print "{0} branch already exists in your local.".format(dev_branch)
            print "Run 'git pull origin {0}' to update your local branch with remote branch.!".format(dev_branch)
            return

        active_branch = get_git_active_branch()
        if active_branch is not source_branch:
            print "You're not in the '{0}' branch. Switching back the branch to '{0}'".format(source_branch)
            try:
                os.system("git checkout {0}".format(source_branch))
            except subprocess.CalledProcessError:
                print "You have uncommitted changes in your local.!"
                print "Please commit your changes or stash them before you can switch branches.!"
                return

        print "Fetching the data from upstream origin..."
        os.system("git fetch origin")

        print "Updating the local repo with origin/latest"
        os.system("git pull origin {0}".format(source_branch))

        print "Creating new branch.!"
        os.system("git checkout -b {0}".format(dev_branch))

        print "Setting up the upstream pointers..."
        os.system("git branch --set-upstream-to origin/{0}".format(source_branch))

        print "Development branch created.!"











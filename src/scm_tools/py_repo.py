#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for Python Package Repository
"""
import os
import json
import getpass

import sys

sys.path.append(r"C:\arth_lab\builds\python\logIO\0.0.1")
sys.path.append(r"C:\arth_lab\builds\python\my_python\0.0.1")
sys.path.append(r"C:\arth_lab\builds\python\scm_tools\0.0.1")

from logIO import get_logger
from my_python.system import file_manager
from scm_tools import constants as scm_constants
# from scm_tools import exceptions as scm_exceptions
import exceptions as scm_exceptions

logger = get_logger(__name__)


USERNAME = getpass.getuser()


def get_package_root_from_path(source_path):
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

        With this method you can pass any of following paths and It will return you the Root path of package


    :param source_path:         `str`                       AbsPath for the package
    :return:                    `str`                       Root path of the current package
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

        if scm_constants.package_setup_file in os.listdir(src_path):
            return src_path

        path_checked.append(src_path)
        return _get_root_directory(src_path=os.path.dirname(src_path), path_checked=path_checked)

    root_path = _get_root_directory(src_path=source_path)
    if root_path is None:
        logger.warning("Given path is not a valid project.")
        return None

    return root_path


class AbstractPackageClass(object):
    """
    Abstract class for the common methods
    """

    def __init__(self, name=None, path=None):
        self.package_name = name
        self.package_path = path

    def cd_to_directory(self, path=None):
        """
        change the directory to given path. If no path given then change to directory to
        self.package_path if that exists
        """
        path = path or self.package_path
        if not path:
            logger.warning("Cannot find package path for '{0}'. Enable to run cd_to_directory().".format(self.name))
            return
        return os.chdir(path)

    @property
    def name(self):
        """
        Return the name of the package
        """
        return self.package_name

    @property
    def root_path(self):
        """
        Return the root path of the package.
        """
        return self.package_path

    def is_valid(self):
        """
        Confirm if the current package is a valid scm package or not
        """
        if not os.path.exists(self.package_path):
            logger.warning("'{0}' package doesn't exists in your disk. ".format(self.name))
            return False

        return True

    def get_requirements(self, as_dict=False):
        """
        Return the requirements file or requirement file data as user asked

        :param as_dict:     `bool`          If set to true then requirements will get return as dict
                                             otherwise the abspath of the requirements file will return
        """
        if not self.is_valid():
            return None

        file_path = os.path.join(self.package_path, scm_constants.requirements_file)
        if not os.path.isfile(file_path):
            logger.warning("Cannot find requirements file for '{0}' at '{1}' path.".format(self.name, file_path))
            return None

        if as_dict:
            # TODO: add functionality for as_dict
            return None

        return file_path

    def get_scm_config(self, as_dict=False):
        """
        Return the scm_conf file or scm_conf file data as user asked

        :param as_dict:     `bool`          If set to true then scm_conf will get return as dict
                                             otherwise the abspath of the scm_conf file will return
        """
        if not self.is_valid():
            return None

        file_path = os.path.join(self.package_path, scm_constants.PACKAGE_CONFIG_FILE)
        if not os.path.isfile(file_path):
            logger.warning("Cannot find scm_conf file for '{0}' at '{1}' path.".format(self.name, file_path))
            return None

        if as_dict:
            # TODO: add functionality for as_dict
            return None

        return file_path

    def get_setup_file(self):
        """
        Return the package setup file for the current package
        """
        package_setup = os.path.join(self.package_path, "package_setup.py")
        if not os.path.isfile(package_setup):
            print "File not found"
            return None

        return package_setup

    def get_bin_directory(self):
        """
        Returns the bin (scripts) directory for the current project where all
        the executable files are.

        Use this path to add to your $PATH for your system when you're adding
        this package in the system config.
        """
        bin_dir = os.path.join(self.get_src_directory(), "bin")
        if os.path.exists(bin_dir):
            return bin_dir
        return None

    def get_src_directory(self):
        """
        Returns the src (source) directory for the current project where all
        actual source code lives.

        Add this path to your $PYTHONPATH for your system when you're adding
        this package in the system config.
        """
        src_dir = os.path.join(self.package_path, "src")
        if os.path.exists(src_dir):
            return src_dir
        return None


class PackageBuilder(AbstractPackageClass):
    """
    Python class for package installation and deletion from the disk

    This class will have methods for scm_install and scm_remove
    """
    def __init__(self, name=None, path=None, ignore_root_path_check=False):
        """
        The logic for the constructor here should be as

        root_path = check for the root directory for given path.
        if not root_path:
            if root path not found then check if user has asked to skip for
            validation check, If user has asked to skip, just skip it otherwise
            raise the PackageNotFoundError to the user.

        finally all good here, you can just call up the parent class
        with respective arguments

        """
        root = get_package_root_from_path(source_path=path)
        if root:
            self._validation_passed = True
        else:
            self._validation_passed = False
            if not ignore_root_path_check:
                raise scm_exceptions.PackageNotFoundError()
            logger.warning("User has asked to skip the root_path check for '{0}' package".format(name))
            root = path

        super(PackageBuilder, self).__init__(name=name, path=root)

    def _is_valid_path(self, file_path):
        """
        Check if the given path is any of the invalid file type in the given scm_constants.py

        :param file_path:           `str`           abs file path
        :return:                    `bool`          returns True if is valid file otherwise False
        """
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[-1]
            if ext in scm_constants.INVALID_FORMATS:
                return False

        for token in scm_constants.INVALID_FORMATS:
            if token == str(file_path):
                return False

            if token in str(file_path):
                return False

        return True

    def _install_binary_files(self, version, to_path=None, symlink=False, overwrite=False):
        """
        Copy over the binary files to the bin path for the project

        :param version:         `str`           Name of the version number. Not Applicable for symlink installation
        :param to_path:         `str`           where do you want to install, defaults to build/qc_build directory
        :param symlink:         `bool`          If set to True, symlink will get created
        :param overwrite:       `bool`          Overwrite existing installed packages.

        :return                 `bool`          True if success else False
        """
        if not self._validation_passed:
            logger.error("Cannot run method as root_path not found for '{0}' package".format(self.name))
            return False

        binary_path = self.get_bin_directory()
        if not binary_path:
            logger.warning("Cannot install as binary_path not found for '{0}' package".format(self.name))
            return False

        install_dir = scm_constants.BIN_TESTING_DIR if symlink else scm_constants.BIN_BUILDS_DIR
        install_dir = to_path or os.path.join(install_dir, self.name, version, "bin")

        if not os.path.isdir(install_dir):
            os.makedirs(install_dir)

        existing_files = list()
        for bin_file in os.listdir(binary_path):
            src_file_path = os.path.join(binary_path, bin_file)
            dst_file_path = os.path.join(install_dir, bin_file)

            if os.path.exists(dst_file_path) and not overwrite:
                existing_files.append(dst_file_path)
                continue

            if symlink:
                logger.debug("Installing for testing: '{0}' >>> '{1}' ".format(src_file_path, dst_file_path))
                file_manager.create_symlinks(source=src_file_path, destination=dst_file_path)
            else:
                logger.debug("Installing package: '{0}' >>> '{1}' ".format(src_file_path, dst_file_path))
                file_manager.copy_files(src_path=src_file_path, dst_path=dst_file_path)

        if existing_files:
            msg = "Some file(s) already exists in the destination. Please use overwrite flag to overwrite them."
            logger.warning(msg)

        return True

    def install_to_disk(self, version, to_path=None, symlink=False, overwrite=False):
        """
        Compile the source code and generate a skeleton for production use.

        :param version:         `str`           Name of the version number. Not Applicable for symlink installation
        :param to_path:         `str`           where do you want to install, defaults to build/qc_build directory
        :param symlink:         `bool`          If set to True, symlink will get created
        :param overwrite:       `bool`          Overwrite existing installed packages.

        :return                 `bool`          True if success else False
        """
        if not self._validation_passed:
            logger.error("Cannot run method as root_path not found for '{0}' package".format(self.name))
            return False

        self._install_source_modules(version=version, to_path=to_path, symlink=symlink, overwrite=overwrite)
        self._install_binary_files(version=version, to_path=to_path, symlink=symlink, overwrite=overwrite)

        package_setup = self.get_setup_file()
        if package_setup:
            import imp
            setup_mod = imp.load_source("setup", package_setup)

    def _install_source_modules(self, version, to_path=None, symlink=False, overwrite=False):
        """
        Compile the source code and generate a skeleton for production use.

        :param version:         `str`           Name of the version number. Not Applicable for symlink installation
        :param to_path:         `str`           where do you want to install, defaults to build/qc_build directory
        :param symlink:         `bool`          If set to True, symlink will get created
        :param overwrite:       `bool`          Overwrite existing installed packages.

        :return                 `bool`          True if success else False
        """
        logger.debug("Installing source modules for '{0}' package".format(self.name))
        if not self._validation_passed:
            logger.error("Cannot run method as root_path not found for '{0}' package".format(self.name))
            return False

        source_path = self.get_src_directory()
        if not source_path:
            logger.warning("Cannot install as source_dir not found for '{0}' package".format(self.name))
            return False

        if symlink:
            # if user asked for installing the package just in the test suite,
            # We need to create a symlink so that user can do continuous tests
            installation_path = to_path or os.path.join(scm_constants.PY_TESTING_DIR, self.name)
            file_manager.create_symlinks(source=source_path, destination=installation_path, overwrite=overwrite)
            return True

        # Let's build and install everything in the PY_BUILDS directory
        installation_path = to_path or os.path.join(scm_constants.PY_BUILDS_DIR, self.name, version)
        if not os.path.isdir(installation_path):
            os.makedirs(installation_path)

        logger.debug("Installation Source Path: {0}".format(source_path))
        logger.debug("Installation Destination Path: {0}".format(installation_path))

        for root, dirs, files in os.walk(source_path):
            if not self._is_valid_path(file_path=root):
                continue

            for each_file in files:
                if not self._is_valid_path(file_path=each_file):
                    continue

                file_path = os.path.join(root, each_file)
                dest_path = file_path.replace(source_path, installation_path)
                logger.debug("Installing : {0}".format(dest_path))
                file_manager.copy_files(src_path=file_path, dst_path=dest_path, overwrite=overwrite)

        logger.debug("Installation completed for source modules for '{0}' package".format(self.name))

    def remove_from_disk(self, symlink=False):
        raise RuntimeError("This needs to be implemented.")


class VersionController(AbstractPackageClass):
    """ Git handler for the package """
    def __init__(self, name=None, path=None, from_git=False):
        super(VersionController, self).__init__(name=name, path=path)
        self.from_git = from_git

    def clone(self, branch_name=None):
        pass

    def rebase(self, with_branch=None):
        pass

    def develop(self, from_branch=None, new_branch_name=None):
        pass

    def push(self, to_branch=None, need_rebase=None, pull_request=False):
        pass


class PythonPackage(AbstractPackageClass):
    """
    Main class to call by the end user


    package = PythonPackage()

    package.isValid()
    package.build(for_test=True)
    package.remove()

    package.rebase(with_branch)
    package.push(create_pr)
    package.develop()

    """
    def __init__(self, name=None, path=None, from_git=False):
        super(PythonPackage, self).__init__(name=name, path=path)

        self.package_builder = PackageBuilder(name=name, path=path)
        self.version_controller = VersionController(name=name, path=path, from_git=from_git)

    def build(self, version, for_test=False, overwrite=False):
        return self.package_builder.install_to_disk(version=version, symlink=bool(for_test), overwrite=overwrite)

    def remove(self):
        # For now no need to provide functionality for removing package from
        # official build directory. This require some work with permissions.
        return self.package_builder.remove_from_disk(symlink=True)

    def rebase(self, with_branch):
        return self.version_controller.rebase(with_branch=with_branch)

    def develop(self, from_branch, new_branch_name):
        return self.version_controller.develop(from_branch=from_branch, new_branch_name=new_branch_name)

    def clone(self, branch_name):
        return self.version_controller.clone(branch_name=branch_name)

    def push(self, to_branch, pull_request):
        return self.version_controller.push(to_branch=to_branch, pull_request=pull_request)

    @classmethod
    def from_path(cls, path):
        pass


class X(object):
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
    obj = PythonPackage(name="scm_tools", path=r"C:\arth_lab\sources\python\scm_tools")
    obj.build(version="0.0.1", for_test=False, overwrite=True)


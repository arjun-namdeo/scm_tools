# -*- coding: utf-8 -*-

"""
General Utility module for SCM_TOOLS
"""
import os
from logIO import get_logger
from my_python.system import file_manager

from . import constants as scm_constants

logger = get_logger(__name__)


def is_valid_path(file_path):
    """
    Check if the given path is any of the invalid file type in the given constants.py

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


def scm_install_package(source, for_qc=False, override=False):
    """
    Compile the source code and generate a skeleton for production use.
    This method will take your active directory and

    :param source:                                  s
    :param for_qc:
    :param override:            `bool`              Override old files.?
    :return:
    """
    if for_qc:
        # if user asked for installing the package just in the test suite,
        # We need to create a symlink so that user can do continuous tests
        # with his code
        installation_path = os.path.join(scm_constants.PY_TESTING_DIR, os.path.basename(source))
        file_manager.create_symlinks(source=source, destination=installation_path, override=override)
        return True

    # Let's build and install everything in the PY_BUILDS directory
    installation_path = os.path.join(scm_constants.PY_BUILDS_DIR, os.path.basename(source))
    if not os.path.isdir(installation_path):
        os.makedirs(installation_path)

    for root, dirs, files in os.walk(source):
        if not is_valid_path(file_path=root):
            continue

        for each_file in files:
            if not is_valid_path(file_path=each_file):
                continue

            file_path = os.path.join(root, each_file)
            dest_path = file_path.replace(source, installation_path)
            logger.debug("Installing : '{0}'".format(each_file))
            file_manager.copy_files(src_path=file_path, dst_path=dest_path)


def scm_install_bin_files(bin_directory, for_qc=False, override=False):
    """
    Compile the source code and generate a skeleton for production use.
    This method will take your active directory and

    :param bin_directory:                                  s
    :param for_qc:
    :param override:            `bool`              Override old files.?
    :return:
    """
    if not os.path.isdir(bin_directory):
        logger.warning("Expected a bin/script directory. Found file.!")
        return False

    install_dir = scm_constants.BIN_TESTING_DIR if for_qc else scm_constants.BIN_BUILDS_DIR

    existing_files = list()
    for bin_file in os.listdir(bin_directory):
        src_file_path = os.path.join(bin_directory, bin_file)
        dst_file_path = os.path.join(install_dir, bin_file)

        if os.path.exists(dst_file_path) and not override:
            existing_files.append(dst_file_path)
            continue

        if for_qc:
            logger.info("Installing for testing: '{0}' >>> '{1}' ".format(src_file_path, dst_file_path))
            file_manager.create_symlinks(source=src_file_path, destination=dst_file_path)
        else:
            logger.info("Installing package: '{0}' >>> '{1}' ".format(src_file_path, dst_file_path))
            file_manager.copy_files(src_path=src_file_path, dst_path=dst_file_path)

    if existing_files:
        msg = "File(s) already exists in the destination place. Please use force/override command to overwrite them."
        logger.info(msg)

    return True


def get_latest_version(package, auto_increment=True):
    """
    Get the latest build version number for given package, Usually this func will be helpful
    when we want to install things in version controlled evn

    :param package:             `PyProject`             Python Project object or full_path of the project
    :param auto_increment:      `bool`                  Do you want to auto increment the version and give you that.?

    :return:
                         `str`      If the package is valid and latest i.e. 1.4.6
                         `None`     If the package is not a valid py project

    """
    if isinstance(package, str):
        from my_python.common.general import get_project_root_from_path
        package = get_project_root_from_path(source_path=package)
        if not package:
            logger.error("Cannot validate the given package", exc_info=True)
            return




if __name__ == "__main__":
    scm_install_package(source=r"C:\arth-lab\sources\prod-test_", for_qc=True)


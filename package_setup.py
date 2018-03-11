#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setting up the current package for use
before using the package, You need to run this module so that
It can configure the whole package for your running env
"""
import os
import sys

from logIO import get_logger
from my_python.common.general import get_project_root_from_path


logger = get_logger(__name__)

logger.info("Running setup...")
package_directory = get_project_root_from_path(__file__).root_path
if not package_directory:
    logger.warning("Valid project files not found in the current path.")
    sys.exit(0)

# setup the PYTHON and BIN path for process
PYTHON_ROOT = os.path.join(package_directory, "src", os.path.basename(package_directory))
BIN_ROOT = os.path.join(package_directory, "src/bin")


# Now check if user has given any other arguments for installation and all
if sys.argv:
    logger.debug("Arguments given for package_setup: {0}".format(sys.argv))

    if "install" in sys.argv:
        logger.debug("Installing package files...")

        _py, process, live, override = sys.argv
        from scm_tools.common import scm_install_package, scm_install_bin_files

        if os.path.exists(PYTHON_ROOT):
            logger.debug("Installing python files from : '{0}'".format(PYTHON_ROOT))
            scm_install_package(PYTHON_ROOT, for_qc=eval(live), override=eval(override))

        if os.path.exists(BIN_ROOT):
            logger.debug("Installing script/bin files from : '{0}'".format(BIN_ROOT))
            scm_install_bin_files(bin_directory=BIN_ROOT, for_qc=eval(live), override=eval(override))

logger.info("Setup completed for '{0}' package.".format(os.path.basename(package_directory)))


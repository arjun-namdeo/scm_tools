#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Custom Exceptions for scm package
"""


class AbstractException(Exception):
    """
    Abstract exception class for Facility-wide usage. This should be subclassed.
    """
    pass


class PackageNotFoundError(AbstractException):
    """
    Exception when the package doesn't found in given path or give git url
    """
    def __init__(self, msg="Package not found in given path/url. Please check your inputs"):
        super(PackageNotFoundError, self).__init__(msg)



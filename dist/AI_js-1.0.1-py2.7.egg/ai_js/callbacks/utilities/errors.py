"""
Error reporting
"""
import sys, traceback


def raise_error(message=""):
    packaged_data = {"utilities.errors.raise_error": {"message": message}}
    print "ERROR", packaged_data
    return packaged_data

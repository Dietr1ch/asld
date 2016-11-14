"""
Filesystem utils
"""
from glob import iglob

def get_files(pattern="*", directory="", recursive=True):
    """
    Directories are also files!
    """
    if directory and directory[-1] != '/':
        directory += '/'

    return iglob(directory+pattern, recursive=recursive)


def get_subdirs(directory=""):
    """
    Iterates over sub-directories
    """
    return get_files("*/", directory)


def get_json_files(directory=""):
    """
    Finds all json files in a directory
    """
    return get_files("**/*.json", directory)

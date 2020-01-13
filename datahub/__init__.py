"""
Defines package metadata.

Be careful not to pull in anything Django-related here (this may complicate access to the
metadata defined below).
"""
from pathlib import PurePath


version_file_path = PurePath(__file__).parent / 'VERSION'

with open(version_file_path) as file:
    __version__ = file.read().strip()

import glob
from pathlib import PurePath


IGNORED_FILES = {'.gitignore', '_template.md.jinja2', 'README.md'}
ROOT_PATH = PurePath(__file__).parents[2]


def list_news_fragments():
    """Return a list of files that are probable news fragments."""
    changelog_files = glob.iglob(f'{ROOT_PATH}/changelog/**/*')
    return set(changelog_files) - IGNORED_FILES

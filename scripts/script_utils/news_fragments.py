from pathlib import Path, PurePath


IGNORED_FILES = {'.gitignore', '_template.md.jinja2', 'README.md'}
ROOT_PATH = PurePath(__file__).parents[2]
CHANGELOG_ROOT = ROOT_PATH / 'changelog'


def list_news_fragments():
    """Return a list of files that are probable news fragments."""
    changelog_path = Path(CHANGELOG_ROOT)
    return {
        path for path in _list_files_recursively(changelog_path)
        if path.name not in IGNORED_FILES
    }


def _list_files_recursively(path):
    for child_path in path.iterdir():
        if child_path.is_dir():
            yield from _list_files_recursively(child_path)
        else:
            yield child_path

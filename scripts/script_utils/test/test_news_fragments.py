from pathlib import PurePath

from script_utils.news_fragments import list_news_fragments


def test_list_news_fragments(monkeypatch):
    """
    Test that list_news_fragments():

    - picks up news fragments in the root changelog directory
    - picks up news fragments in the changelog sub-directories
    - picks up misnamed news fragments
    - excludes ignored files
    """
    changelog_root = PurePath(__file__).parent / 'fake_repo' / 'changelog'
    monkeypatch.setattr('script_utils.news_fragments.CHANGELOG_ROOT', changelog_root)

    absolute_paths = list_news_fragments()
    relative_paths = {
        str(path.relative_to(changelog_root))
        for path in absolute_paths
    }
    assert relative_paths == {
        'misnamed.fragment.feature',
        'root-test.feature.md',
        'adviser/adviser-test.feature.md',
    }

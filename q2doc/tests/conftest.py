import os
import shutil
import pytest
from sphinx.testing.path import path

collect_ignore = ['roots']
pytest_plugins = 'sphinx.testing.fixtures'


@pytest.fixture(scope='session')
def rootdir():
    """Sets root folder for sphinx unit tests."""
    return path(__file__).parent.abspath() / 'roots'


def _initialize_test_directory(session):
    if 'SPHINX_TEST_TEMPDIR' in os.environ:
        tempdir = os.path.abspath(os.getenv('SPHINX_TEST_TEMPDIR'))
        print('Temporary files will be placed in %s.' % tempdir)

        if os.path.exists(tempdir):
            shutil.rmtree(tempdir)

        os.makedirs(tempdir)


def pytest_sessionstart(session):
    _initialize_test_directory(session)

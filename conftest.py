import os

import pytest
from sphinx.testing.path import path

pytest_plugins = 'sphinx.testing.fixtures'


@pytest.fixture(scope='session')
def rootdir():
    """Sets root folder for sphinx unit tests."""
    return path('.').abspath() / 'q2doc' / 'tests' / 'roots'

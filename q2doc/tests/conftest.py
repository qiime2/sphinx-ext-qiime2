import os

import pytest
from sphinx.testing.path import path

pytest_plugins = 'sphinx.testing.fixtures'


@pytest.fixture(scope='session')
def rootdir():
    """ Sets root folder for sphinx unit tests """
    return path(os.path.dirname(__file__) or '.').abspath() / 'roots'

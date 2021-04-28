import pathlib
import textwrap

import pytest
from sphinx.testing.path import path



collect_ignore = ['roots']
pytest_plugins = 'sphinx.testing.fixtures'


@pytest.fixture(scope='function')
def rootdir():
    """Sets root folder for sphinx unit tests."""
    return path(__file__).parent.abspath() / 'roots'


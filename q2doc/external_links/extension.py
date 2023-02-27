# ----------------------------------------------------------------------------
# Copyright (c) 2020-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import pathlib
import pkg_resources

from sphinx.util.fileutil import copy_asset


def copy_asset_files(app, pagename, templatename, context, doctree):
    base_fp = pkg_resources.resource_filename('q2doc', 'external_links')
    asset_path = pathlib.Path(base_fp) / 'assets'

    for path in asset_path.glob('*.js'):
        copy_asset(str(path), os.path.join(app.outdir, '_static'))
        app.add_js_file(str(path.name))

    for path in asset_path.glob('*.css'):
        copy_asset(str(path), os.path.join(app.outdir, '_static'))
        app.add_css_file(str(path.name))


def setup(app):
    app.connect('html-page-context', copy_asset_files)
    return {'version': '0.0.1'}

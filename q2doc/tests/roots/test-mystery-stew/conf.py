from sphinx.application import Sphinx
import sys
import pathlib

import qiime2

root = pathlib.Path(__file__).parent.absolute()
sys.path.insert(0, str(root))

master_doc = "index"
extensions = [
    'q2doc.question',
    'q2doc.qiime1',
    'q2doc.checkpoint',
    'q2doc.command_block',
    'q2doc.usage',
    'q2doc.external_links',
]

source_suffix = '.rst'
project = 'QIIME 2'
copyright = '2016-2020, QIIME 2 development team'
author = 'QIIME 2 development team'
version = qiime2.__release__
release = qiime2.__version__
language = None
pygments_style = 'sphinx'
html_sidebars = {
    "**": ['globaltoc.html', 'searchbox.html']
}
html_show_sourcelink = False
htmlhelp_basename = 'QIIME2doc'
latex_documents = [
    (master_doc, 'QIIME2.tex', 'QIIME 2 Documentation',
     'QIIME 2 development team', 'manual'),
]
man_pages = [
    (master_doc, 'qiime2', 'QIIME 2 Documentation',
     [author], 1)
]
texinfo_documents = [
    (master_doc, 'QIIME2', 'QIIME 2 Documentation',
     author, 'QIIME2', 'One line description of project.',
     'Miscellaneous'),
]
linkcheck_timeout = 15
mathjax_path = ('https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.2/'
                'MathJax.js?config=TeX-AMS-MML_HTMLorMML')

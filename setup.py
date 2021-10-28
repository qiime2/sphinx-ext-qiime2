# ----------------------------------------------------------------------------
# Copyright (c) 2020-2021, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------


from setuptools import setup, find_packages

setup(
    name='sphinx-ext-qiime2',
    packages=find_packages(),
    license='BSD-3-Clause',
    url='https://qiime2.org',
    include_package_data=True,
    package_data={
        'sphinx_ext_qiime2': ['./*/templates/*']
    },
)

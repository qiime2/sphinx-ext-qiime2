# ----------------------------------------------------------------------------
# Copyright (c) 2020, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------


from setuptools import setup, find_packages

setup(
    name='q2doc',
    packages=find_packages(),
    license='BSD-3-Clause',
    url='https://qiime2.org',
    include_package_data=True,
    package_data={
        'q2doc': ['./*/templates/*']
    },
)

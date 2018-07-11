#!/usr/bin/env python

# Copyright (C) 2017 ARCO Group
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import sys
from setuptools import setup, find_packages


def local_open(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))


exec(open('version.py').read())


packages = find_packages()
if sys.platform == "win32":
    packages += ['slice']


config = dict(
    name         = 'libcitisim',
    version      = __version__,
    description  = 'Python bindings for CITISIM',
    author       = 'Arco Research Group',
    author_email = 'David.Villa@gmail.com',
    url          = 'https://bitbucket.org/arco_group/prj.citisim',
    license      = 'GPLv3',
    packages     = packages,
    provides     = ['libcitisim'],
    classifiers  = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)

# include slices for Windows distrib
if sys.platform == "win32":
    config['package_data'] = {'': ['*.ice']}
    config['include_package_data'] = True

setup(**config)

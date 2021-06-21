#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:39

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

import setuptools

setuptools.setup(name='icua',
      version='0.0.1',
      description='',
      url='https://github.com/dicelab-rhul/pystarworlds',
      author='Benedict Wilkins',
      author_email='brjw@hotmail.co.uk',
      license='',
      packages=setuptools.find_packages(),
      install_requires = [ 'pystarworlds>=0.0.3', 'icu' ],
      classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 2 - Pre-Alpha",
        "Operating System :: OS Independent",
    ])

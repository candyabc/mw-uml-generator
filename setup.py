#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os


from setuptools import setup, find_packages


def fpath(name):
    return os.path.join(os.path.dirname(__file__), name)


def read(fname):
    return open(fpath(fname)).read()


def desc():
    info = read('README.rst')
    try:
        return info + '\n\n' + read('doc/changelog.rst')
    except IOError:
        return info

# grep flask_admin/__init__.py since python 3.x cannot import it before using 2to3
file_text = read(fpath('mw_uml_generator/__init__.py'))


def grep(attrname):
    pattern = r"{0}\W*=\W*'([^']+)'".format(attrname)
    strval, = re.findall(pattern, file_text)
    return strval


entry_points = """
[console_scripts]
pycli = mw_uml_generator.cli:cli
"""
install_requires = [
]

setup(
    name='mw-uml-generator',
    version=grep('__version__'),
    url='',
    license=grep('__license__'),
    author=grep('__author__'),
    author_email=grep('__email__'),
    description='generate code tool',
    long_description=desc(),
    packages=find_packages(),
    entry_points=entry_points,
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=install_requires,

    tests_require=[
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)



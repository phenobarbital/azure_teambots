#!/usr/bin/env python
"""Azure Teams Bot.

Azure Teams Bot is a Facility for deploying MS Teams Bots.
See:
https://github.com/phenobarbital/azure_teambots
"""
import ast
from os import path
from setuptools import find_packages, setup

def get_path(filename):
    return path.join(path.dirname(path.abspath(__file__)), filename)


def readme():
    with open(get_path('README.md'), 'r', encoding='utf-8') as rd:
        return rd.read()


version = get_path('azure_teambots/version.py')
with open(version, 'r', encoding='utf-8') as meta:
    t = compile(meta.read(), version, 'exec', ast.PyCF_ONLY_AST)
    for node in (n for n in t.body if isinstance(n, ast.Assign)):
        if len(node.targets) == 1:
            name = node.targets[0]
            if isinstance(name, ast.Name) and \
                    name.id in (
                        '__version__',
                        '__title__',
                        '__description__',
                        '__author__',
                        '__license__', '__author_email__'):
                v = node.value
                if name.id == '__version__':
                    __version__ = v.s
                if name.id == '__title__':
                    __title__ = v.s
                if name.id == '__description__':
                    __description__ = v.s
                if name.id == '__license__':
                    __license__ = v.s
                if name.id == '__author__':
                    __author__ = v.s
                if name.id == '__author_email__':
                    __author_email__ = v.s

COMPILE_ARGS = ["-O3"]

setup(
    name='azure_teambots',
    version=__version__,  # pylint: disable=E0601
    python_requires=">=3.9.16",
    url='https://github.com/phenobarbital/azure_teambots',
    description=__description__,  # pylint: disable=E0601
    long_description=readme(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ],
    author='Jesus Lara',
    author_email='jesuslarag@gmail.com',
    packages=find_packages(
        exclude=[
            'contrib',
            'google',
            'docs',
            'plugins',
            'lab',
            'examples',
            'samples',
            'settings',
            'etc',
            'bin',
            'build'
        ]
    ),
    include_package_data=True,
    package_data={"azure_teambots": ["py.typed"]},
    license=__license__,  # pylint: disable=E0601
    license_files='LICENSE',
    setup_requires=[
        "setuptools==74.0.0",
        "Cython==3.0.11",
        "wheel==0.44.0"
    ],
    install_requires=[
        "transitions>=0.9.2",
        "botbuilder-core==4.17.0",
        "botbuilder-integration-aiohttp==4.17.0",
        "botbuilder-schema==4.17.0",
        "botbuilder-dialogs==4.17.0",
        "botframework-streaming==4.17.0",
        "msal==1.32.0",
        "msgraph-core==1.3.2",
        "azure-identity==1.20.0",
        "helpers==0.2.0",
        "navconfig>=1.7.13",
        "navigator-api>=2.13.5",
    ],
    zip_safe=False,
    project_urls={  # Optional
        'Source': 'https://github.com/phenobarbital/azure_teambots',
        'Tracker': 'https://github.com/phenobarbital/azure_teambots/issues',
        'Documentation': 'https://github.com/phenobarbital/azure_teambots/',
        'Funding': 'https://paypal.me/phenobarbital',
        'Say Thanks!': 'https://saythanks.io/to/phenobarbital',
    },
)

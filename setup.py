#!/usr/bin/env python
"""Azure Teams Bot.

Azure Teams Bot is a Facility for deploying MS Teams Bots.
See:
https://github.com/phenobarbital/azure_teambots
"""
import ast
from os import path
from setuptools import find_packages, setup, Extension
from Cython.Build import cythonize

def get_path(filename):
    return path.join(path.dirname(path.abspath(__file__)), filename)


def readme():
    with open(get_path('README.md'), 'r', encoding='utf-8') as rd:
        return rd.read()


version = get_path('azure_teams_bot/version.py')
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

COMPILE_ARGS = ["-O2"]

# extensions = [
#     Extension(
#         name='querysource.types.mapping',
#         sources=['querysource/types/mapping.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c"
#     ),
#     Extension(
#         name='querysource.parsers.abstract',
#         sources=['querysource/parsers/abstract.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c"
#     ),
#     Extension(
#         name='querysource.parsers.parser',
#         sources=['querysource/parsers/parser.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c"
#     ),
#     Extension(
#         name='querysource.parsers.sql',
#         sources=['querysource/parsers/sql.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c"
#     ),
#     Extension(
#         name='querysource.exceptions',
#         sources=['querysource/exceptions.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c"
#     ),
#     Extension(
#         name='querysource.libs.json',
#         sources=['querysource/libs/json.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c++"
#     ),
#     Extension(
#         name='querysource.utils.parseqs',
#         sources=['querysource/utils/parseqs.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c++"
#     ),
#     Extension(
#         name='querysource.types.typedefs',
#         sources=['querysource/types/typedefs.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#     ),
#     Extension(
#         name='querysource.types.validators',
#         sources=['querysource/types/validators.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c++"
#     ),
#     Extension(
#         name='querysource.types.converters',
#         sources=['querysource/types/converters.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c++"
#     ),
#     Extension(
#         name='querysource.utils.functions',
#         sources=['querysource/utils/functions.pyx'],
#         extra_compile_args=COMPILE_ARGS,
#         language="c++"
#     )
# ]


setup(
    name='azure_teams_bot',
    version=__version__,
    python_requires=">=3.9.16",
    url='https://github.com/phenobarbital/azure_teambots',
    description=__description__,
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
    package_data={"querysource": ["py.typed"]},
    license=__license__,
    license_files='LICENSE',
    setup_requires=[
        "wheel==0.42.0",
        "Cython==3.0.6",
        "asyncio==3.4.3",
    ],
    install_requires=[
        "transitions==0.9.0",
        "botbuilder-core==4.16.1",
        "botbuilder-integration-aiohttp==4.16.1",
        "botbuilder-schema==4.16.1",
        "botbuilder-dialogs==4.16.1",
        "helpers==0.2.0",
        "python-datamodel>=0.6.28",
        "navconfig>=1.7.0",
        "navigator-api>=2.10.0",
    ],
    tests_require=[
        'pytest>=5.4.0',
        'coverage',
        'pytest-asyncio',
        'pytest-xdist',
        'pytest-assume'
    ],
    # ext_modules=cythonize(extensions),
    zip_safe=False,
    project_urls={  # Optional
        'Source': 'https://github.com/phenobarbital/azure_teambots',
        'Tracker': 'https://github.com/phenobarbital/azure_teambots/issues',
        'Documentation': 'https://github.com/phenobarbital/azure_teambots/',
        'Funding': 'https://paypal.me/phenobarbital',
        'Say Thanks!': 'https://saythanks.io/to/phenobarbital',
    },
)

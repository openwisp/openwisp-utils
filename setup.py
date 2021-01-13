#!/usr/bin/env python
import os
import sys

from openwisp_utils import get_version
from setuptools import find_packages, setup

if sys.argv[-1] == 'publish':
    # delete any *.pyc, *.pyo and __pycache__
    os.system('find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf')
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload -s dist/*")
    os.system("rm -rf dist build")
    args = {'version': get_version()}
    print("You probably want to also tag the version now:")
    print("  git tag -a %(version)s -m 'version %(version)s'" % args)
    print("  git push --tags")
    sys.exit()


setup(
    name='openwisp-utils',
    version=get_version(),
    license='BSD-3-Clause',
    author='Rohith Asrk',
    author_email='rohith.asrk@gmail.com',
    description='OpenWISP 2 Utilities',
    long_description=open('README.rst').read(),
    url='http://openwisp.org',
    download_url='https://github.com/openwisp/openwisp-utils/releases',
    platforms=['Platform Independent'],
    keywords=['django', 'netjson', 'openwrt', 'networking', 'openwisp'],
    packages=find_packages(exclude=['tests*', 'docs*']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'checkmigrations = openwisp_utils.qa:check_migration_name',
            'checkcommit = openwisp_utils.qa:check_commit_message',
            'checkrst = openwisp_utils.qa:check_rst_files',
        ]
    },
    scripts=['openwisp-qa-check', 'openwisp-qa-format'],
    zip_safe=False,
    install_requires=['django-model-utils>=4.0.0,<4.1.0'],
    extras_require={
        'qa': [
            'black<=19.10b0',
            'flake8<=3.9',
            'isort~=5.0',
            'readme-renderer~=28.0',
            'coveralls~=3.0.0',  # depends on coverage as well
        ],
        'rest': [
            'djangorestframework>=3.11,<3.12',
            'django-filter>=2.2.0<2.4.0',
            'drf-yasg~=1.20.0',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: System :: Networking',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
    ],
)

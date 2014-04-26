#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

import sys

f = open('README.rst')
long_description = f.read().strip()
f.close()

setup(
    name='askbot-fedmsg',
    version='0.1.0',
    description="Askbot plugin for emitting events to the Fedora message bus",
    long_description=long_description,
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='http://github.com/fedora-infra/askbot-fedmsg/',
    license='LGPLv2+',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    py_modules=['askbot_fedmsg'],
    install_requires=[
        'fedmsg',
        'askbot',
    ],
    include_package_data=True,
    zip_safe=False,
)

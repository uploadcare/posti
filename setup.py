#!/usr/bin/env python

from setuptools import setup

setup(
    name="posti",
    version="1.0",
    author="Uploadcare",
    author_email="ak@uploadcare.com",
    description="Runs heavy writers in seperate thread and returns readable interface",
    keywords="async io blocking",
    url="https://github.com/uploadcare/posti",
    py_modules=['posti'],
)

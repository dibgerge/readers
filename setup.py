#! python
from setuptools import setup, find_packages

setup(name='readers',
      version='0.1.0',
      author='Gerges Dib',
      author_email='dibgerge@gmail.com',
      packages=['readers'],
      entry_points={'console_scripts': ['readers=readers.cli:cli']},
      install_requires=['numpy', 'pandas', 'xarray'],
      classifiers=['Programming Language :: Python :: 3.6']
      )


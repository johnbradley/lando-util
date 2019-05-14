import os
import sys
from setuptools import setup
# version checking derived from https://github.com/levlaz/circleci.py/blob/master/setup.py
from setuptools.command.install import install

VERSION = '0.5.0'
TAG_ENV_VAR = 'CIRCLE_TAG'


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv(TAG_ENV_VAR)

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


setup(name='lando-util',
      version=VERSION,
      description='Utility functions for https://github.com/Duke-GCB/lando',
      url='http://github.com/Duke-GCB/lando-util',
      license='MIT',
      packages=['lando_util', 'lando_util.organize_project'],
      install_requires=[
          'click==7.0',
          'Jinja2==2.10.1',
          'DukeDSClient==2.1.4',
          'humanfriendly==2.4',
          'python-dateutil==2.6.0',
          'Markdown==2.6.9',
          'PyYAML==5.1',
      ],
      zip_safe=False,
      cmdclass={
          'verify': VerifyVersionCommand,
      },
      )

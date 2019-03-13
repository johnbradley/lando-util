from setuptools import setup

setup(name='lando-util',
      version='0.3.1',
      description='Utility functions for https://github.com/Duke-GCB/lando',
      url='http://github.com/Duke-GCB/lando-util',
      license='MIT',
      packages=['lando_util'],
      install_requires=[
          'click==7.0',
          'Jinja2==2.10',
          'DukeDSClient==2.1.1',
          'humanfriendly==2.4',
          'python-dateutil==2.6.0',
          'Markdown==2.6.9',
          'PyYAML==3.12',
      ],
      zip_safe=False)

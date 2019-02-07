from setuptools import setup

setup(name='lando-util',
      version='0.1',
      description='Test',
      url='http://github.com/Duke-GCB/lando-util',
      license='MIT',
      packages=['lando_util'],
      install_requires=[
          'click==7.0',
          'Jinja2==2.10',
          'DukeDSClient==2.1.1',
      ],
      zip_safe=False)

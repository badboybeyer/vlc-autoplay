import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from os import path

if sys.version_info[:2] < (3, 6):
    msg = ("VLC Autoplay requires Python 3.6 or later. "
           "You are using version %s.  Please "
           "install using a supported version." % sys.version)
    sys.stderr.write(msg)
    sys.exit(1)

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Utilities',
    'Topic :: Multimedia :: Video',
    'Topic :: Internet',
    'Topic :: Communications',
    ]

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='vlc-autoplay',
      version='0.1c',
      description='Add media from a library rando-magically to a VLC playlist using the RC or telnet interface',
      long_description=long_description,
      long_description_content_type='text/markdown',      
      license='GNU GPLv3',
      url='https://github.com/badboybeyer/vlc-autoplay',
      author='Erich Beyer',
      author_email='erich@beyerautomation.com',
      maintainer='Erich Beyer',
      maintainer_email='erich@beyerautomation.com',
      classifiers=CLASSIFIERS,
      packages=['vlc_autoplay'],
      install_requires=[
          'python-magic',
      ],      
      entry_points={
          'console_scripts': [
              'connect_and_add_media=vlc_autoplay.connect_and_add_media:main',
          ]
      },      
      project_urls={
          'Source': 'https://github.com/badboybeyer/vlc-autoplay'
      },      
      )

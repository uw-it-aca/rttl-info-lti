import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/rttl-info-lti>`_.
"""

version_path = 'rttlinfo/VERSION'
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='UW-RTTL-Info-LTI',
    version=VERSION,
    packages=['rttlinfo'],
    include_package_data=True,
    install_requires=[
        'Django~=4.2',
        'django-blti~=3.0',
        'django-compressor',
        'uw-memcached-clients~=1.0',
        'UW-RestClients-SWS',
    ],
    license='Apache License, Version 2.0',
    description='An LTI application that displays RTTL resources and status',
    long_description=README,
    url='https://github.com/uw-it-aca/rttl-info-lti',
    author="UW-IT SETS",
    author_email="aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)

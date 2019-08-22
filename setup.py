import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
#    'plaster_pastedeploy',
    'pyramid',
    'pyramid_retry',
    'pyramid_tm',
    'pyramid_zodbconn',
    'pyramid_session_redis',
    'transaction',
    'ZODB3',
    'arche',
    'peppercorn',
    'cornice',
    'cornice_swagger',
    'colander',
    'colander_jsonschema',
    'pyyaml',
    'authomatic',
    'pytz',
    'redis',
    'awesome-slugify',
]

tests_require = [
    'nose',
    'coverage',
    'webtest',
    'fakeredis'
]

setup(
    name='kedja_server',
    version='0.1.0',
    description='Kedja Server',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='',
    author_email='',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages('src', exclude=['tests']),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = kedja:main',
        ],
    },
)

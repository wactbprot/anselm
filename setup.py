"""setup.py based on
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='anselm',
    version='0.1.0',
    description='Read out launcher, setup store, REST-Api.',
    long_description=long_description,
    url='https://a75436.berlin.ptb.de/vaclab/anselm',
    author='Thomas Bock',
    author_email='thomas.bock@ptb.de',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: vaclab team',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='Vacuum, Pressure, Gauges',
    packages=find_packages(exclude=['docs',
                                    'tests',
                                    ]),
    install_requires=[
                    'couchdb',
                    'PyQt5',
                    'coloredlogs',
                    'redis',
                    'flask',
                    ],
    #extras_require={
    #    'dev': ['sphinx',
    #            'sphinx_rtd_theme',
    #            'autopep8',
    #            'PyUnitReport',
    #            ],
    #},
    #package_data={
    #    'sample': ['test_doc'],
    #},
    # entry_points={
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
)

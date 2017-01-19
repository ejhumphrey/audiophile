import imp
from setuptools import setup

description = \
    """Audiophile - A flexible I/O library for audio files in Python."""

version = imp.load_source('audiophile.version', 'audiophile/version.py')

setup(
    name='audiophile',
    version=version.version,
    description=description,
    author='Eric J. Humphrey',
    author_email='humphrey.eric@gmail.com',
    url='http://github.com/ejhumphrey/audiophile',
    download_url='http://github.com/ejhumphrey/audiophile/releases',
    packages=['audiophile'],
    package_data={},
    classifiers=[
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5"
    ],
    keywords='audio',
    license='ISC',
    install_requires=[
        'numpy >= 1.8.0',
        'nose',
        'six'
    ]
)

from setuptools import setup

description = \
    """Claudio -- A Concise Little Audio library for getting audio samples into
    and out of Python."""

setup(
    name='claudio',
    version='0.1.0',
    description=description,
    author='Eric J. Humphrey',
    author_email='humphrey.eric@gmail.com',
    url='http://github.com/ejhumphrey/claudio',
    download_url='http://github.com/ejhumphrey/claudio/releases',
    packages=['claudio'],
    package_data={},
    classifiers=[
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7"
    ],
    keywords='machine learning, neural network',
    license='ISC',
    install_requires=[
        'numpy >= 1.8.0',
        'scipy >= 0.13.0'
    ]
)

# audiophile

A flexible I/O library for audio files in Python.

[![Build Status](https://travis-ci.org/ejhumphrey/audiophile.svg?branch=master)](https://travis-ci.org/ejhumphrey/audiophile)
[![Coverage Status](https://coveralls.io/repos/github/ejhumphrey/audiophile/badge.svg?branch=master)](https://coveralls.io/github/ejhumphrey/audiophile?branch=master)

## Why?

Why _another_ audio file library? There are two (and a half) reasons you may want to use `audiophile` (over audioread):

- *We use SoX under the hood:* SoX is nice, fast, and codec support is diverse. You should use it.
- *Frame-based generators*: Audio signals are often (easily) processed in frames / windows / blocks of samples. Because blocks are yielded as read, `audiophile` can handle arbitrarily long audio files, which might be challenging for long (≈hours) recordings.
- (Coming soon) *Abstracted overlap-and-add file-writing*: It is on the roadmap (admittedly, without a timeline) to provide a simple interface for writing blocks of audio back to a rolling buffer.

## Installation

The easiest way to install `audiophile` is with pip:

```
$ pip install git+git://github.com/ejhumphrey/audiophile.git
```

Alternatively, you can clone the repository and do it the hard way:

```
$ cd ~/to/a/good/place
$ git clone https://github.com/ejhumphrey/audiophile.git
$ cd audiophile
$ python setup.py build
$ [sudo] python setup.py install
```

## Testing your install

Clone the repository and run the tests directly; `nose` is recommended, and installed as a dependency:

```
$ cd {wherever_you_cloned_it}/audiophile
$ nosetests
```

## Usage

... more to come // see the tests in the meantime ...

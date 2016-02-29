"""Utilities to call ffmpeg from Python.

For more information, refer to https://www.ffmpeg.org/
"""
from __future__ import print_function

import logging
import os
import subprocess

import claudio.formats as formats
import claudio.util as util

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = OSError

logging.basicConfig(level=logging.DEBUG)

# Error Message for SoX
__NO_FFMPEG__ = """ffmpeg could not be found!

    If you do not have ffmpeg, proceed here:
     - - - https://www.ffmpeg.org/ - - -

    If you do (or think that you should) have ffmpeg, double-check your
    path variables."""


class FFMpegError(BaseException):
    pass


def __BIN__():
    return 'ffmpeg'


def _check():
    """Test for FFMpeg.

    Returns
    -------
    success : bool
        True if it looks like ffmpeg exists.
    """
    try:
        info = subprocess.check_output([__BIN__(), '-version'])
        status = 'ffmpeg version' in str(info)
        message = __NO_FFMPEG__
    except (FileNotFoundError, subprocess.CalledProcessError) as derp:
        status = False
        message = __NO_FFMPEG__ + "\n{}".format(derp)
    if status:
        logging.info(message)
    else:
        logging.warning(message)
    return status


def check_ffmpeg():
    """Assert that SoX is present and can be called."""
    if not _check():
        raise FFMpegError("SoX check failed.\n{}".format(__NO_FFMPEG__))


def convert(input_file, output_file,
            samplerate=None, channels=None, bytedepth=None):
    """Converts one audio file to another on disk.

    Parameters
    ----------
    input_file : str
        Input file to convert.

    output_file : str
        Output file to writer.

    samplerate : float, default=None
        Desired samplerate. If None, defaults to the same as input.

    channels : int, default=None
        Desired channels. If None, defaults to the same as input.

    bytedepth : int, default=None
        Desired bytedepth. If None, defaults to the same as input.

    Returns
    -------
    status : bool
        True on success.
    """
    args = ['-i', input_file]

    if bytedepth:
        raise NotImplementedError("Haven't gotten here yet.")
    if channels:
        args += ['-ac', str(channels)]
    if samplerate:
        args += ['-ar', str(samplerate)]

    args += [output_file, '-y']

    return ffmpeg(args)


def ffmpeg(args):
    """Pass an argument list to ffmpeg.

    Parameters
    ----------
    args : list
        Argument list for ffmpeg.

    Returns
    -------
    success : bool
        True on successful calls to ffmpeg.
    """
    check_ffmpeg()
    util.validate_clargs(args)
    args = [__BIN__()] + list(args)

    try:
        logging.debug("Executing: {}".format(args))
        process_handle = subprocess.Popen(args, stderr=subprocess.PIPE)
        status = process_handle.wait()
        logging.debug(process_handle.stdout)
        return status == 0
    except OSError as error_msg:
        logging.error("OSError: ffmpeg failed! {}".format(error_msg))
    except TypeError as error_msg:
        logging.error("TypeError: {}".format(error_msg))
    return False


def is_valid_file_format(input_file):
    """Determine if a given file is supported by FFMPEG based on its
    extension.

    Parameters
    ----------
    input_file : str
        Audio file to verify for support.

    Returns
    -------
    status : bool
        True if supported.
    """
    raise NotImplementedError("Come back to this.")
    # File extension
    file_ext = os.path.splitext(input_file)[-1]
    # Return False if the file lacks an extension.
    if not file_ext:
        return False
    # Remove dot-separator.
    file_ext = file_ext.strip(".")
    # Pure wave support
    if file_ext == formats.WAVE:
        return True

    # Otherwise, check against SoX.
    else:
        check_ffmpeg()
        info = str(subprocess.check_output([__BIN__(), '-codecs']))
        valid = file_ext in info
        if valid:
            logging.debug("FFMpeg supports '{}' files.".format(file_ext))
        else:
            logging.debug("SoX does not support '{}' files.".format(file_ext))

        return valid

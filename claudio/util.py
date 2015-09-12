"""Utility methods for claudio."""

import numpy as np
import struct
import tempfile as tmp


def byte_string_to_array(byte_string, channels, bytedepth):
    """Convert a byte string into a numpy array.

    Parameters
    ----------
    byte_string : str
        raw byte string
    channels : int
        number of channels to unpack from frame
    bytedepth : int
        byte-depth of audio data

    Returns
    -------
    array : np.ndarray of floats
        array with shape (num_samples, channels), bounded on [-1.0, 1.0)
    """
    # Number of values per channel.
    N = len(byte_string) / channels / bytedepth
    # Assume 2-byte encoding.
    fmt = 'h'
    if bytedepth == 3:
        tmp = list(byte_string)
        byte_string = "".join(
            [tmp.insert(n * 4 + 3, struct.pack('b', 0)) for n in range(N)])

    if bytedepth in [3, 4]:
        fmt = "i"

    array = np.array(struct.unpack('%d%s' % (N, fmt) * channels, byte_string))
    return array.reshape([N, channels]) / (2.0 ** (8 * bytedepth - 1))


def array_to_byte_string(array, bytedepth):
    """Convert a numpy array to a byte string.

    Parameters
    ----------
    array : np.ndarray
        Array with shape (N, channels), bounded on [-1.0, 1.0). It will,
        however, gracefull broadcast a 1D-array.
    bytedepth : int
        Byte-depth of audio data.

    Returns
    -------
    byte_string : str
        A raw byte string.
    """
    if array.ndim == 1:
        array = array[:, np.newaxis]
    if not array.ndim == 2:
        raise ValueError("Arg 'array' must satisfy array.ndim in [1, 2].")
    if bytedepth == 3:
        # TODO: Fix this.
        raise ValueError("Known error writing bytedepth=3 strings.")

    channels = array.shape[1]
    # Number of total values.
    N = array.shape[0] * channels
    data = (array.flatten() * np.power(2.0, 8 * bytedepth - 1)).astype(int)
    # Assume 2-byte
    fmt = "h"
    if bytedepth in [3, 4]:
        fmt = "i"

    return struct.pack("%d%s" % (N, fmt), *data)


def temp_file(ext):
    """Generate a temporary file path with read/write permissions.

    Parameters
    ----------
    ext: str
        Extension for the temporary file.

    Returns
    -------
    tmpfile : string
        A writeable file path.
    """
    return tmp.mktemp(suffix=".%s" % ext.strip("."), dir=tmp.gettempdir())


def classy_print(cls, msg):
    """Return a message string with the name of the given class as a prefix.

    Parameters
    ----------
    cls : class
        Must inherit from object.
    msg : str, or string-like
        Arbitrary string message.
    """
    return "{0} :: {1}".format(cls.__name__, msg)

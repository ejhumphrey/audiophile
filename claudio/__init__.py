import logging
import numpy as np

logging.basicConfig(level=logging.CRITICAL)

from .fileio import read
from .fileio import write
from . import pywave
from . import sox
from . import util
from .version import version as __version__


def soundsc(signal, samplerate):
    tmp_file = util.temp_file(sox.pywave.WAVE_EXT)
    signal = np.asarray(signal)
    signal *= 0.98 / np.abs(signal).max()
    write(tmp_file, signal, samplerate)
    try:
        sox.play(tmp_file)
    except KeyboardInterrupt:
        pass

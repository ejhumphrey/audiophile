import numpy as np

import claudio.fileio as fileio
import claudio.formats as formats
import claudio.sox as sox
import claudio.util as util


def soundsc(signal, samplerate):
    """Play a signal as a normalized soundwave.

    Parameters
    ----------
    signal : np.ndarray, shape=(num_samples, num_channels)
        Signal to sonify.

    samplerate : scalar
        Samplerate to use for audio playback.
    """
    tmp_file = util.temp_file(formats.WAVE)
    signal = np.asarray(signal)
    signal *= 0.98 / np.abs(signal).max()
    fileio.write(tmp_file, signal, samplerate)
    try:
        sox.play(tmp_file)
    except KeyboardInterrupt:
        pass

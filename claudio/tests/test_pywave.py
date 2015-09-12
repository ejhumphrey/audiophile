import numpy as np

import claudio
from claudio import pywave
from claudio import util


def _generate_wavfile(samplerate):
    wavfile = util.temp_file(pywave.WAVE_EXT)
    claudio.write(wavfile, np.sin(np.arange(20)/100.0), samplerate)
    return wavfile


def test_pywave_open():
    samplerate = 8000
    wavfile = _generate_wavfile(samplerate)
    wav = pywave.open(wavfile)
    assert wav
    assert wav.samplerate() == samplerate

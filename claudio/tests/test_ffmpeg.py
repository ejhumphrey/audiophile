import pytest
import six
import wave

import claudio.ffmpeg as ffmpeg
import claudio.formats as formats
import claudio.util as util


@pytest.fixture()
def sample_wav():
    input_file = util.temp_file(formats.WAVE)
    samplerate = 1000
    channels = 1
    bytedepth = 2

    wave_handle = wave.open(input_file, mode="w")
    wave_handle.setframerate(samplerate)
    wave_handle.setnchannels(channels)
    wave_handle.setsampwidth(bytedepth)

    # Corresponds to [0.0, 0.5, 0.0, -0.5], or a sine-wave at
    # half-Nyquist. This should sound tonal, for debugging.
    wave_handle.writeframes(six.b("\x00\x00\x00@\x00\x00\x00\xc0") * 200)
    wave_handle.close()
    return input_file


def __true(a):
    assert bool(a)


def __eq(a, b):
    assert a == b


def test___BIN__():
    assert ffmpeg.__BIN__()


def test_ffmpeg__check():
    assert ffmpeg._check()


def test_ffmpeg_check_ffmpeg():
    ffmpeg.check_ffmpeg()


def test_ffmpeg_convert(sample_wav):
    fout = util.temp_file(formats.WAVE)
    fin = str(sample_wav)
    for kwargs in [dict(), dict(samplerate=2000), dict(channels=2)]:
        assert ffmpeg.convert(fin, output_file=fout, **kwargs)

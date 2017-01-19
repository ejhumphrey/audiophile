"""Unittests for audiophile.

TODO: Update this to py.test, fixtures and standalone methods. This is pretty
old-school right here.
"""

import unittest
import numpy as np
import os
import six
import tempfile
import wave

import audiophile.formats as formats
import audiophile.fileio as fileio
import audiophile.util as util


class FileIOTests(unittest.TestCase):
    input_file = util.temp_file(formats.WAVE)
    samplerate = 440
    channels = 1
    bytedepth = 2
    num_repeats = 110
    test_dir = os.path.dirname(__file__)

    def setUp(self):
        "Generate a wave file for testing."
        self.wave_handle = wave.open(self.input_file, mode="w")
        self.wave_handle.setframerate(self.samplerate)
        self.wave_handle.setnchannels(self.channels)
        self.wave_handle.setsampwidth(self.bytedepth)

        # Corresponds to [0.0, 0.5, 0.0, -0.5], or a sine-wave at
        # half-Nyquist. This should sound tonal, for debugging.
        self.wave_handle.writeframes(
            six.b('\x00\x00\x00@\x00\x00\x00\xc0') * self.num_repeats)
        self.wave_handle.close()

    def test_AudioFile_params(self):
        af = fileio.AudioFile(self.input_file, mode='r')
        self.assertEqual(
            af.samplerate, self.samplerate, "Samplerate mismatch.")
        self.assertEqual(
            af.channels, self.channels, "Channel mismatch.")
        self.assertEqual(
            af.bytedepth, self.bytedepth, "Byte depth mismatch.")
        self.assertEqual(
            af.filepath, self.input_file, "Filepath mismatch.")
        self.assertEqual(
            af.num_samples, self.num_repeats * 4, "Sample count mismatch.")

    def test_AudioFile_new_params(self):
        new_samplerate = 4000
        new_channels = 2
        new_bytedepth = 1
        af = fileio.AudioFile(self.input_file,
                              samplerate=new_samplerate,
                              channels=new_channels,
                              bytedepth=new_bytedepth,
                              mode='r')
        self.assertEqual(
            af.samplerate, new_samplerate, "Samplerate mismatch.")
        self.assertEqual(
            af.channels, new_channels, "Channel mismatch.")
        self.assertEqual(
            af.bytedepth, new_bytedepth, "Byte depth mismatch.")

    def test_FramedAudioFile_set_framerate(self):
        framerate = 10
        overlap = 0.6
        stride = 40
        af = fileio.FramedAudioFile(self.input_file,
                                    samplerate=400,
                                    framesize=100,
                                    framerate=framerate)
        self.assertEqual(
            af.framerate, framerate, "Framerate mismatch.")
        self.assertEqual(
            af.overlap, overlap, "Overlap mismatch.")
        self.assertEqual(
            af.stride, stride, "Stride mismatch.")

    def test_FramedAudioFile_set_stride(self):
        framerate = 10
        overlap = 0.6
        stride = 40
        af = fileio.FramedAudioFile(self.input_file,
                                    samplerate=400,
                                    framesize=100,
                                    stride=stride)
        self.assertEqual(
            af.framerate, framerate, "Framerate mismatch.")
        self.assertEqual(
            af.overlap, overlap, "Overlap mismatch.")
        self.assertEqual(
            af.stride, stride, "Stride mismatch.")

    def test_FramedAudioFile_set_overlap(self):
        framerate = 10
        overlap = 0.6
        stride = 40
        af = fileio.FramedAudioFile(self.input_file,
                                    samplerate=400,
                                    framesize=100,
                                    overlap=overlap)
        self.assertEqual(
            af.framerate, framerate, "Framerate mismatch.")
        self.assertEqual(
            af.overlap, overlap, "Overlap mismatch.")
        self.assertEqual(
            af.stride, stride, "Stride mismatch.")

    def test_FramedAudioReader_read_center_aligned(self):
        af = fileio.FramedAudioReader(self.input_file,
                                      framesize=8,
                                      alignment='center',
                                      overlap=0.5)
        frame_0 = np.array([0, 0, 0, 0, 0, 0.5, 0, -0.5]).reshape(8, 1)
        frame_n = np.array([0, 0.5, 0, -0.5, 0, 0.5, 0, -0.5]).reshape(8, 1)
        for i, frame_act in enumerate(af):
            err_msg = "Frame-%d mismatch." % i
            if i == 0:
                np.testing.assert_array_equal(
                    frame_act, frame_0, err_msg, True)
            else:
                np.testing.assert_array_equal(
                    frame_act, frame_n, "Frame-%d mismatch." % i, True)

    def test_FramedAudioReader_read_left_aligned(self):
        af = fileio.FramedAudioReader(self.input_file,
                                      framesize=8,
                                      alignment='left',
                                      overlap=0.5)
        frame_exp = np.array([0, 0.5, 0, -0.5, 0, 0.5, 0, -0.5]).reshape(8, 1)
        frame_end = np.array([0, 0.5, 0, -0.5, 0, 0, 0, 0]).reshape(8, 1)
        for i, frame_act in enumerate(af):
            err_msg = "Frame-%d mismatch." % i
            if i == (self.num_repeats - 1):
                np.testing.assert_array_equal(
                    frame_act, frame_end, err_msg, True)
            else:
                np.testing.assert_array_equal(
                    frame_act, frame_exp, err_msg, True)

    def test_read_real_wave(self):
        wav_file = os.path.join(self.test_dir, 'sample.wav')
        signal, samplerate = fileio.read(wav_file)
        assert len(signal)
        assert samplerate

    def test_read_real_aiff(self):
        aiff_file = os.path.join(self.test_dir, 'sample.aiff')
        signal, samplerate = fileio.read(aiff_file)
        assert len(signal)
        assert samplerate

    def test_write_wave(self):
        wav_file = os.path.join(self.test_dir, 'sample.wav')
        x, fs1 = fileio.read(wav_file)

        tmp = tempfile.NamedTemporaryFile(suffix='.wav')
        fileio.write(tmp.name, x, fs1)
        y, fs2 = fileio.read(tmp.name)
        np.testing.assert_array_almost_equal(x, y)
        assert fs1 == fs2


def test_read_empty_wav():
    sfile = os.path.join(os.path.dirname(__file__), 'empty.wav')
    signal, samplerate = fileio.read(sfile)
    assert len(signal) == 0
    assert samplerate


if __name__ == "__main__":
    unittest.main()

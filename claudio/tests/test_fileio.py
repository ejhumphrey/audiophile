import unittest
import numpy as np

from claudio import fileio
from claudio import pywave
from claudio import util


class FileIOTests(unittest.TestCase):
    input_file = util.temp_file(pywave.WAVE_EXT)
    samplerate = 440
    channels = 1
    bytedepth = 2
    num_repeats = 110

    def setUp(self):
        "Generate a wave file for testing."
        self.wave_handle = pywave.open(self.input_file, mode="w")
        self.wave_handle.set_samplerate(self.samplerate)
        self.wave_handle.set_channels(self.channels)
        self.wave_handle.set_bytedepth(self.bytedepth)

        # Corresponds to [0.0, 0.5, 0.0, -0.5], or a sine-wave at
        # half-Nyquist. This should sound tonal, for debugging.
        self.wave_handle.writeframes(
            "\x00\x00\x00@\x00\x00\x00\xc0" * self.num_repeats)
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


if __name__ == "__main__":
    unittest.main()

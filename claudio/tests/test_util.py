import unittest
import numpy as np

import claudio.util as util


class EncodingTest(unittest.TestCase):

    def setUp(self):
        self.mono = np.array([0.0, 0.5, -0.5])
        self.stereo = np.array([[0, -0.5], [0.5, 0.5], [-0.5, 0.0]])
        self.mono_str2 = "\x00\x00\x00@\x00\xc0"
        self.mono_str4 = "\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\xc0"
        self.stereo_str2 = "\x00\x00\x00\xc0\x00@\x00@\x00\xc0\x00\x00"
        self.stereo_str4 = "\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00@" + \
                           "\x00\x00\x00@\x00\x00\x00\xc0\x00\x00\x00\x00"

    def tearDown(self):
        pass

    def test_array_to_byte_string_mono_bytedepthE2(self):
        self.assertEqual(util.array_to_byte_string(self.mono, 2),
                         self.mono_str2)

    def test_array_to_byte_string_mono_bytedepthE4(self):
        self.assertEqual(util.array_to_byte_string(self.mono, 4),
                         self.mono_str4)

    def test_byte_string_to_array_mono_bytedepthE2(self):
        np.testing.assert_array_equal(
            util.byte_string_to_array(
                self.mono_str2, channels=1, bytedepth=2).flatten(),
            self.mono,
            verbose=True)

    def test_byte_string_to_array_mono_bytedepthE4(self):
        np.testing.assert_array_equal(
            util.byte_string_to_array(
                self.mono_str4, channels=1, bytedepth=4).flatten(),
            self.mono,
            verbose=True)

    def test_array_to_byte_string_stereo_bytedepthE2(self):
        self.assertEqual(util.array_to_byte_string(self.stereo, 2),
                         self.stereo_str2)

    def test_array_to_byte_string_stereo_bytedepthE4(self):
        self.assertEqual(util.array_to_byte_string(self.stereo, 4),
                         self.stereo_str4)

    def test_byte_string_to_array_stereo_bytedepthE2(self):
        np.testing.assert_array_equal(
            util.byte_string_to_array(self.stereo_str2,
                                      channels=2, bytedepth=2),
            self.stereo,
            verbose=True)

    def test_byte_string_to_array_stereo_bytedepthE4(self):
        np.testing.assert_array_equal(
            util.byte_string_to_array(self.stereo_str4,
                                      channels=2, bytedepth=4),
            self.stereo,
            verbose=True)

    # TODO(ejhumphrey): More unit-tests...
    # - 3-byte depth
    # - multi-channel support

if __name__ == "__main__":
    unittest.main()

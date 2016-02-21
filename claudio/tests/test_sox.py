import os
import unittest
import six
import wave

import claudio.formats as formats
import claudio.sox as sox
import claudio.util as util


class SoxTests(unittest.TestCase):
    input_file = util.temp_file(formats.WAVE)
    samplerate = 1000
    channels = 1
    bytedepth = 2

    @classmethod
    def setUp(self):
        "Generate a local wave file for testing sox."
        self.wave_handle = wave.open(self.input_file, mode="w")
        self.wave_handle.setframerate(self.samplerate)
        self.wave_handle.setnchannels(self.channels)
        self.wave_handle.setsampwidth(self.bytedepth)

        # Corresponds to [0.0, 0.5, 0.0, -0.5], or a sine-wave at
        # half-Nyquist. This should sound tonal, for debugging.
        self.wave_handle.writeframes(
            six.b("\x00\x00\x00@\x00\x00\x00\xc0") * 200)
        self.wave_handle.close()

    def test_formats(self):
        self.assertEqual(sox.is_valid_file_format("some.wav"),
                         True,
                         "Wav check failed.")
        self.assertEqual(sox.is_valid_file_format("booger"),
                         False,
                         "Extension-less format failed.")
        self.assertEqual(sox.is_valid_file_format("curious.george"),
                         False,
                         "Invalid extension failed.")

    def test_convert_samplerate(self):
        output_file = util.temp_file(formats.WAVE)
        self.assert_(
            sox.convert(input_file=self.input_file,
                        output_file=output_file,
                        samplerate=self.samplerate / 2,
                        channels=self.channels,
                        bytedepth=self.bytedepth),
            "Conversion with different samplerate failed.")
        wav_handle = wave.open(output_file, mode='r')
        self.assertEqual(self.samplerate / 2,
                         wav_handle.getframerate(),
                         "Samplerate conversion failed.")

    def test_convert_format(self):
        output_file = os.path.splitext(self.input_file)[0] + ".aif"
        self.assert_(
            sox.convert(input_file=self.input_file,
                        output_file=output_file,
                        samplerate=self.samplerate / 2,
                        channels=self.channels,
                        bytedepth=self.bytedepth),
            "Conversion to .aif failed.")

    def test_trim(self):
        output_file = util.temp_file(formats.WAVE)
        self.assert_(
            sox.trim(input_file=self.input_file,
                     output_file=output_file,
                     start_time=0,
                     end_time=0.1),
            "Conversion failed.")


if __name__ == "__main__":
    unittest.main()

"""Interfaces for dealing with audio files."""

import logging
import numpy as np
import os
import scipy.io.wavfile as _spwav

from claudio import sox
from claudio import pywave
from claudio import util


class AudioFile(object):
    """Abstract AudioFile base class."""

    def __init__(self, filepath, samplerate=None, channels=None,
                 bytedepth=None, mode="r"):
        """Base class for interfacing with audio files.

        When writing audio files, samplerate, channels, and bytedepth must be
        specified. Otherwise, these parameters may be None when reading to use
        the default values of the audio file.

        filepath : str
            Absolute path to a sound file. Does not need to exist (yet).
        samplerate : float, default=None
            Samplerate for the audio file.
        channels : int, default=None
            Number of channels for the audio file.
        bytedepth : int, default=None
            bytedepth (in bytes) of the returned file. For example, CD-quality
            audio has a bytedepth of 2 (16-bit).
        mode : str, default='r'
            Open the file for [r]eading or [w]riting.
        """
        logging.debug(util.classy_print(AudioFile, "Constructor."))
        assert sox.is_valid_file_format(filepath)
        if mode == "w":
            assert samplerate, "Writing audiofiles requires a samplerate."
            assert channels, "Writing audiofiles requires channels."
            assert bytedepth, "Writing audiofiles requires a bytedepth."

        self._filepath = filepath
        self._wave_handle = None
        self._temp_filepath = util.temp_file(pywave.WAVE_EXT)

        self._mode = mode
        logging.debug(util.classy_print(AudioFile, "Opening wave file."))
        self.__get_handle__(self.filepath, samplerate, channels, bytedepth)
        logging.debug(util.classy_print(AudioFile, "Success!"))

    def __get_handle__(self, filepath, samplerate, channels, bytedepth):
        """Get hooks into a wave object for reading or writing.

        Parameters
        ----------
        filepath : str
        samplerate : float
        channels : int
        bytedepth : int

        On success, creates an open wave file handle corresponding to filepath,
        or a tempfile after a successful SoX conversion.

        Note: This could probably be pulled out into a standalone function, but
        using class members makes this a little cleaner. Something to consider.
        """
        self._CONVERT = False
        if self._mode == 'r':
            try:
                self._wave_handle = pywave.open(filepath, 'r')
                if bytedepth and self._wave_handle.bytedepth() != bytedepth:
                    self._CONVERT = True
                if samplerate and self._wave_handle.samplerate() != samplerate:
                    self._CONVERT = True
                if channels and self._wave_handle.channels() != channels:
                    self._CONVERT = True
            except pywave.Error:
                self._CONVERT = True
            if self._CONVERT:
                assert sox.convert(input_file=filepath,
                                   output_file=self._temp_filepath,
                                   samplerate=samplerate,
                                   bytedepth=bytedepth,
                                   channels=channels), \
                    "SoX Conversion failed for '%s'." % filepath
                self._wave_handle = pywave.open(self._temp_filepath, 'r')
        else:
            fmt_ext = os.path.splitext(self.filepath)[-1].strip('.')
            if fmt_ext == pywave.WAVE_EXT:
                self._wave_handle = pywave.open(self.filepath, self._mode)
            else:
                # To write out non-wave files, need a temp wave object first.
                self._CONVERT = True
                self._wave_handle = pywave.open(
                    self._temp_filepath, self._mode)
            # Set file parameters
            self._wave_handle.set_samplerate(samplerate)
            self._wave_handle.set_bytedepth(bytedepth)
            self._wave_handle.set_channels(channels)

    def reset(self):
        """
        Set the file's read pointer back to zero & take care of
        initialization.

        Returns
        -------
        None
        """
        self._EOF = False

    def close(self):
        """Explicit destructor."""
        logging.debug(util.classy_print(AudioFile, "Cleaning up."))
        if self._wave_handle:
            self._wave_handle.close()
        if self._mode == 'w' and self._CONVERT:
            logging.debug(
                util.classy_print(AudioFile,
                                  "Conversion required for writing."))

            assert sox.convert(input_file=self._temp_filepath,
                               output_file=self.filepath,
                               samplerate=self.samplerate,
                               bytedepth=self.bytedepth,
                               channels=self.channels)
        if self._temp_filepath and os.path.exists(self._temp_filepath):
            logging.debug(util.classy_print(AudioFile,
                                            "Temporary file deleted."))
            os.remove(self._temp_filepath)

    def __del__(self):
        """Implicit destructor."""
        self.close()

    @property
    def samplerate(self):
        """
        Returns
        -------
        samplerate : float
        """
        return float(self._wave_handle.samplerate())

    @property
    def channels(self):
        """
        Returns
        -------
        channels : int
            number of audio channels
        """
        return self._wave_handle.channels()

    @property
    def bytedepth(self):
        """
        Returns
        -------
        bytedepth : int
            bytes per sample
        """
        return self._wave_handle.bytedepth()

    @property
    def filepath(self):
        """
        Returns
        -------
        filepath : string
            Source file path of this audio file.
        """
        return self._filepath

    @property
    def wavefile(self):
        """Return the filename of the active (opened) wave file.
        """
        if self._CONVERT:
            return self._temp_filepath
        else:
            return self._filepath

    @property
    def num_samples(self):
        """
        Returns
        -------
        num_samples : int
            Total duration in samples of this file.
        """
        return self._wave_handle.num_samples()

    @property
    def duration(self):
        """
        Returns
        -------
        duration : scalar
            Total time duration of this file.
        """
        return self.num_samples / self.samplerate


class FramedAudioFile(AudioFile):
    """TODO(ejhumphrey): Write me."""

    def __init__(self, filepath, framesize,
                 samplerate=None, channels=None, bytedepth=None, mode='r',
                 time_points=None, framerate=None, stride=None, overlap=0.5,
                 alignment='center', offset=0):
        """Frame-based audio file parsing.

        Parameters
        ----------
        filepath : str
            Absolute path to an audio file.
        framesize : int
            Size of each frame of audio, as (num_samples, num_channels).
        samplerate : int, default = as-is
            Desired sample rate.
        channels : int, default = as-is
            Desired number of channels.
        bytedepth : int, default = as-is
            Desired byte depth.
        mode : str, default='r'
            Open the file for [r]eading or [w]riting.
        time_points : array_like
            Iteritable of absolute points in time to align frames.
        framerate : scalar, default = None
            Uniform frequency to advance frames from the given file.
        stride : int, default = None
            Integer number of samples to advance frames.
        overlap : scalar, default = 0.5
            Percent overlap between adjacent frames.
        alignment : str, default = 'center'
            Controls alignment of the frame, one of ['left','center','right'].
        offset : scalar, default = 0
            Time in seconds to shift the alignment of a frame.

        For frame-based audio processing, there are a few roughly equivalent
        ways of defining how to advance through the data. The order of
        preference for these strategies is defined as follows:
        1. time_points : Explicit checkpoints in time to read or write a frame
            of audio, subject to alignment and offset parameters. This can
            gracefully handle asynchronous, un-ordered framing with no
            guarantee of the relationship between time points. Additionally,
            this is independent of both samplerate and framesize, which allows
            those parameters to change without affecting the frame-based
            process.
        2. framerate : Framing with a constant frequency in Hz, i.e. M frames
            per second. This is also samplerate and framesize independent.
        3. stride : Constant number of samples to advance between frames. This
            is independent of framesize but not samplerate, i.e. different
            samplerates will yield a different framerate, which may or may not
            be what you actually want.
        4. overlap, default = 0.5 (50% overlap) : This is the simplest approach
            to setting a suitable frame stride, but also arguably the most
            fragile. Frames are produced as both a function of samplerate and
            framesize.

        """
        logging.debug(util.classy_print(FramedAudioFile, "Constructor."))
        AudioFile.__init__(self, filepath, samplerate=samplerate,
                           channels=channels, bytedepth=bytedepth, mode=mode)

        self._framesize = framesize
        self._alignment = alignment
        self._offset = offset
        self._time_points = None
        logging.debug(util.classy_print(FramedAudioFile, "Init Striding."))
        self._init_striding(time_points, framerate, stride, overlap)
        self.reset()

    def _init_striding(self, time_points=None, framerate=None,
                       stride=None, overlap=None):
        """Logic for intializing parameters that control automatically striding
        through frames of audio.

        Parameters (ordered by precedence)
        ----------
        time_points : array_like
            Iteritable of absolute points in time to align frames.
        framerate : scalar, default = None
            Uniform frequency to advance frames from the given file.
        stride : int, default = None
            Integer number of samples to advance frames.
        overlap : scalar, default = 0.5
            Percent overlap between adjacent frames.
        """

        # Frame-advancing hierarchy.
        # 1. Time points - framerate, stride and overlap are undefined.
        if time_points is not None:
            self.time_points = time_points
            self._framerate = None
            self._stride = None
            self._overlap = None
        # 2. Framerate - define stride and overlap in terms of framerate.
        elif framerate and self.samplerate:
            self.framerate = framerate
        # 3. Stride - define framerate and overlap in terms of stride.
        elif stride:
            self.stride = stride
        # 4. Overlap
        elif overlap is not None:
            self.overlap = overlap
        else:
            raise ValueError("All stride-related parameters cannot be None.")

    def reset(self):
        """TODO(ejhumphrey)"""
        logging.debug(util.classy_print(FramedAudioFile, "Reset."))
        AudioFile.reset(self)
        self.framebuffer = np.zeros(self.frameshape)
        self._time_index = 0

    def _compute_uniform_time_points(self):
        """Generate a 1D np.ndarray of uniformly spaced time points, in seconds.

        Returns
        -------
        time_points : np.ndarray
            1D vector of length self.num_frames
        """
        return np.arange(self.num_frames) / self.framerate

    @property
    def time_points(self):
        """TODO(ejhumphrey): Write me."""
        return self._time_points

    @time_points.setter
    def time_points(self, time_points='uniform'):
        """Set a vector of time points for accessing an audio file.
        Alternatively compute this vector if time_points="uniform" given the
        current parameters.

        Parameters
        ----------
        time_points : array_like, or str
            vector of times, or "uniform"
        """

        if time_points == 'uniform':
            # If uniform, compute fixed stride.
            time_points = self._compute_uniform_time_points()

        self._time_points = np.asarray(time_points)
        self._time_index = 0

    @property
    def framesize(self):
        """
        Returns
        -------
        framesize : int
            Number of samples returned per frame
        """
        return self._framesize

    @property
    def frameshape(self):
        """
        Returns
        -------
        shape : tuple
            Tuple of (frame length, number of channels)

        """
        return (self.framesize, self.channels)

    @property
    def alignment(self):
        """
        Returns
        -------
        mode : string
            Alignment mode, one of ['left','center','right']
        """
        return self._alignment

    @property
    def offset(self):
        """Offset in seconds.

        Returns
        -------
        offset : float
            Alignment offset, in seconds.
        """
        return float(self._offset)

    @property
    def framerate(self):
        """
        Returns
        -------
        framerate : float
            Frequency of frames, in Hertz.
        """
        return float(self._framerate)

    @framerate.setter
    def framerate(self, framerate):
        self._time_points = None
        self._framerate = framerate
        self._stride = self.samplerate / self.framerate
        self._overlap = 1.0 - self.stride / self.framesize
        self.time_points = "uniform"

    @property
    def stride(self):
        """Number of samples between frames.

        Returns
        -------
        stride : float
            Fractional stride between frames.
        """
        return float(self._stride)

    @stride.setter
    def stride(self, stride):
        """Set frame stride and update corresponding params."""
        self._time_points = None
        self._stride = stride
        self._framerate = self.samplerate / self.stride
        self._overlap = 1.0 - self.stride / self.framesize
        self.time_points = "uniform"

    @property
    def overlap(self):
        """
        Returns
        -------
        overlap : scalar
            ratio of overlap between frames.
        """
        return self._overlap

    @overlap.setter
    def overlap(self, overlap):
        """
        Returns
        -------
        num_frames : int
            Number of frames in the audiofile.
        """
        self._time_points = None
        self._overlap = overlap
        self._stride = self.framesize * (1.0 - self.overlap)
        self._framerate = self.samplerate / self.stride
        self.time_points = "uniform"

    @property
    def num_frames(self):
        """Determine the number of frames in this audio file.

        Returns
        -------
        num_frames : int
            Number of frames in the audiofile.

        Notes regarding implementation details: This does not make an effort to
        exhaustively stride over an audio file, i.e. convolution with a
        fractional hop-size.
        """
        if self._time_points is None:
            assert self.framerate
            return int(np.ceil(self.duration * self.framerate))
        else:
            return len(self._time_points)

    def _next_time_point(self):
        """Compute the next LEFT-ALIGNED time point given the current
        state of parameters.

        Takes into account the three parameters of absolute index, alignment,
        and offset.
        """
        time_point = self._time_points[self._time_index]
        self._time_index += 1
        if self._time_index == len(self._time_points):
            self._EOF = True

        if self.alignment == 'center':
            time_point -= 0.5 * self.framesize / self.samplerate
        elif self.alignment == 'right':
            time_point -= self.framesize / self.samplerate

        time_point += self.offset
        return time_point

    def _time_point_to_sample_index(self, time_point):
        """Convert a floating-point time to integert samples."""
        return int(np.round(time_point * self.samplerate))


class FramedAudioReader(FramedAudioFile):
    """TODO(ejhumphrey): Write me."""
    def __init__(self, filepath, framesize,
                 samplerate=None, channels=None, bytedepth=None,
                 overlap=0.5, stride=None, framerate=None, time_points=None,
                 alignment='center', offset=0):

        # Always read.
        mode = 'r'
        logging.debug(util.classy_print(FramedAudioReader, "Constructor."))
        self._wave_handle = None
        FramedAudioFile.__init__(self, filepath, framesize, samplerate,
                                 channels, bytedepth, mode, time_points,
                                 framerate, stride, overlap, alignment,
                                 offset)

    def read_frame_at_index(self, sample_index, framesize=None):
        """Read 'framesize' samples starting at 'sample_index'.
        If framesize is None, defaults to current framesize.

        Parameters
        ----------
        sample_index: int
            Index at which to center the frame.
        framesize: int, default=None
            Number of samples to read from the file.
        """
        if not framesize:
            framesize = self.framesize

        frame_index = 0
        frame = np.zeros([framesize, self.channels])

        # Check boundary conditions
        if sample_index < 0 and sample_index + framesize > 0:
            framesize = framesize - np.abs(sample_index)
            frame_index = np.abs(sample_index)
            sample_index = 0
        elif sample_index > self.num_samples:
            return frame
        elif (sample_index + framesize) <= 0:
            return frame

        logging.debug(util.classy_print(
            FramedAudioReader, "sample_index = %d" % sample_index))
        self._wave_handle.setpos(sample_index)
        newdata = util.byte_string_to_array(
            byte_string=self._wave_handle.readframes(int(framesize)),
            channels=self.channels,
            bytedepth=self.bytedepth)

        # Place new data within the frame
        frame[frame_index:frame_index + newdata.shape[0]] = newdata
        return frame

    def read_frame_at_time(self, time_point, framesize=None):
        """Read 'framesize' samples around at `time_point`, in seconds.
        If framesize is None, defaults to current framesize.

        Parameters
        ----------
        time_point : scalar
            Point in time at which to align the frame.
        framesize: int, default=None
            Number of samples to read from the file.
        """
        return self.read_frame_at_index(
            self._time_point_to_sample_index(time_point), framesize)

    def next(self):
        if not self._EOF:
            return self.read_frame_at_time(self._next_time_point())
        else:
            self.reset()
            raise StopIteration

    def __iter__(self):
        return self


def read(filepath, samplerate=None, channels=None, bytedepth=None):
    """Read the entirety of a sound file into memory.

    Parameters
    ----------
    filepath: str
        Path to an audio file.
    samplerate: scalar, or None for file's default
        Samplerate for the returned audio signal.
    channels: int, or None for file's default
        Number of channels for the returned audio signal.

    Returns
    -------
    signal: np.ndarray
        Audio signal, shaped (num_samples, num_channels).
    samplerate: float
        Samplerate of the audio signal.
    """
    def_framesize = 50000
    reader = FramedAudioReader(
        filepath, framesize=def_framesize, samplerate=samplerate,
        channels=channels, bytedepth=bytedepth, overlap=0, alignment='left')
    signal = np.zeros([reader.num_frames * reader.framesize,
                       reader.channels])
    # Step through the file
    for idx, frame in enumerate(reader):
        signal[idx * reader.framesize:(idx + 1) * reader.framesize] = frame

    return signal[:reader.num_samples], reader.samplerate


def write(filepath, signal, samplerate=44100, bytedepth=2):
    """Write an audio signal to disk.

    Parameters
    ----------
    filepath: str
        Path to an audio file.
    signal : np.ndarray, ndim in [1,2]
        Audio signal to write to disk.
    samplerate: scalar, or None for file's default
        Samplerate for the returned audio signal.
    bytedepth : int, default=2
        Number of bytes for the audio signal; must be 2.
    """
    if bytedepth != 2:
        raise NotImplementedError("Currently only 16-bit audio is supported.")

    tmp_file = util.temp_file(pywave.WAVE_EXT)
    if pywave.WAVE_EXT == os.path.splitext(filepath)[-1].strip('.'):
        tmp_file = filepath

    signal = np.asarray(signal)
    if 'float' in signal.dtype.name:
        dtypes = {2: np.int16}
        signal = np.asarray(signal*np.power(2, 8*bytedepth - 1),
                            dtype=dtypes[bytedepth])

    _spwav.write(filename=tmp_file, data=signal, rate=int(samplerate))

    if tmp_file != filepath:
        sox.convert(tmp_file, filepath)

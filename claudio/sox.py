"""Utilities to call SoX from Python.

For more information, refer to http://sox.sourceforge.net/

Note: Most uncompressed audio formats are supported out of the box. However,
for mp3, aac, mp4, and so forth, various steps must be taken to first build
the codec libraries, and *then* compile sox from source.
"""
from __future__ import print_function

import logging
import os
import subprocess

from . import pywave
from . import util

logging.basicConfig(level=logging.DEBUG)

# Error Message for SoX
__NO_SOX__ = """SoX could not be found!

    If you do not have SoX, proceed here:
     - - - http://sox.sourceforge.net/ - - -

    If you do (or think that you should) have SoX, double-check your
    path variables."""


def _sox_check():
    """Test for SoX."""
    sox_res = subprocess.check_output(['sox', '-h'])
    status = 'SPECIAL FILENAMES' in str(sox_res)
    if not status:
        logging.warning(__NO_SOX__)
    return status


has_sox = _sox_check()


def assert_sox():
    """Assert that SoX is present and can be called."""
    if has_sox:
        return
    assert False, "SoX assertion failed.\n{}".format(__NO_SOX__)


def split_stereo(input_file, output_file_left, output_file_right):
    """Split a stereo file into separate mono files.

    Parameters
    ----------
    input_file : str
        Path to stereo audio file.

    output_file_left : str
        Path to output of left channel.

    output_file_right : float
        Path to output of right channel.

    Returns
    -------
    status : bool
        True on success.
    """
    left_args = ['sox', '-D', input_file, output_file_left, 'remix', '1']
    right_args = ['sox', '-D', input_file, output_file_right, 'remix', '2']
    return sox(left_args) and sox(right_args)


def combine_as_stereo(left_channel, right_channel, output_file):
    """Create a stereo audio file from 2 mono audio files.
    Left goes to channel 1, right goes to channel 2.

    Parameters
    ----------
    left_channel : str
        Path to mono audio file that will be mapped to the left channel.

    right_channel : str
        Path to mono audio file that will be mapped to the right channel.

    output_file : float
        Path to stereo output file.

    Returns
    -------
    status : bool
        True on success.
    """
    return sox(['sox', '-M', left_channel, right_channel, output_file])


def trim(input_file, output_file, start_time, end_time):
    """Excerpt a clip from an audio file, given a start and end time.

    Parameters
    ----------
    input_file : str
        Sound file to trim.

    output_file : str
        File for writing output.

    start_time : float
        Start time of the clip.

    end_time : float
        End time of the clip.

    Returns
    -------
    status : bool
        True on success.
    """
    assert start_time >= 0, "The value for 'start_time' must be positive."
    assert end_time >= 0, "The value for 'end_time' must be positive."
    return sox(['sox', input_file, output_file, 'trim',
                '%0.8f' % start_time, '%0.8f' % (end_time - start_time)])


def pad(input_file, output_file, start_duration=0, end_duration=0):
    """Add silence to the beginning or end of a file.

    Parameters
    ----------
    input_file : str
        Path to audio file.

    output_file : str
        Path to save output to.

    start_duration : float
        Number of seconds of silence to add to beginning.

    end_duration : float
        Number of seconds of silence to add to end.

    Returns
    -------
    status : bool
        True on success.

    """
    assert start_duration >= 0, "Start duration must be positive."
    assert end_duration >= 0, "End duration must be positive."
    return sox(['sox', input_file, output_file, 'pad',
               '%0.8f' % start_duration, '%0.8f' % end_duration])


def fade(input_file, output_file, fade_in_time=1, fade_out_time=8,
         fade_shape='q'):
    """Add a fade in or fade out to an audio file.
    Fade shapes are quarter sine waves. If you care to change this write

    Parameters
    ----------
    input_file : str
        Audio file.

    output_file : str
        File for writing output.

    fade_in_time : float
        Number of seconds of fade in.

    fade_out_time : float
        Number of seconds of fade out.

    fade_shape : str
        Shape of fade. 'q' for quarter sine (default), 'h' for half sine,
        't' for linear, 'l' for logarithmic, or 'p' for inverted parabola.

    Returns
    -------
    status : bool
        True on success.
    """
    fade_shapes = ['q', 'h', 't', 'l', 'p']
    assert fade_shape in fade_shapes, "Invalid fade shape."
    assert fade_in_time >= 0, "Fade in time must be nonnegative."
    assert fade_out_time >= 0, "Fade out time must be nonnegative."
    return sox(['sox', input_file, output_file, 'fade', '%s' % fade_shape,
                '%0.8f' % fade_in_time, '0', '%0.8f' % fade_out_time])


def convert(input_file, output_file,
            samplerate=None, channels=None, bytedepth=None):
    """Converts one audio file to another on disk.

    Parameters
    ----------
    input_file : str
        Input file to convert.

    output_file : str
        Output file to writer.

    samplerate : float, default=None
        Desired samplerate. If None, defaults to the same as input.

    channels : int, default=None
        Desired channels. If None, defaults to the same as input.

    bytedepth : int, default=None
        Desired bytedepth. If None, defaults to the same as input.

    Returns
    -------
    status : bool
        True on success.
    """
    args = ['sox', '--no-dither', input_file]

    if bytedepth:
        assert bytedepth in [1, 2, 3, 4, 8]
        args += ['-b%d' % (bytedepth * 8)]
    if channels:
        args += ['-c %d' % channels]
    if output_file is None:
        output_file = util.temp_file(pywave.WAVE_EXT)

    args += [output_file]

    if samplerate:
        args += ['rate', '-I', '%f' % samplerate]

    return sox(args)


def mix(file_list, output_file):
    """Naively mix (sum) a list of files into one audio file.

    Parameters
    ----------
    file_list : list
        List of paths to audio files.

    output_file : str
        Path to output file.

    Returns
    -------
    status : bool
        True on success.
    """
    args = ["sox", "-m"]
    for fname in file_list:
        args.append(fname)
    args.append(output_file)

    return sox(args)


def concatenate(file_list, output_file):
    """Concatenate a list of files into one audio file.

    Parameters
    ----------
    file_list : list
        List of paths to audio files.

    output_file : str
        Path to output file.

    Returns
    -------
    status : bool
        True on success.
    """
    args = ["sox", "--combine"]
    args.append("concatenate")
    for fname in file_list:
        args.append(fname)
    args.append(output_file)

    return sox(args)


def normalize(input_file, output_file, db_level=-3):
    """Normalize an audio file to a particular db level

    Parameters
    ----------
    input_file : str
        Path to input audio file.

    output_file : str
        Path to output audio file.

    db_level : output volume (db)

    Returns
    -------
    status : bool
        True on success.
    """
    return sox(['sox', "--norm=%f" % db_level, input_file, output_file])


def remove_silence(input_file, output_file,
                   silence_threshold=0.1, min_voicing_duration=0.5):
    """Remove silence from an audio file.

    Parameters
    ----------
    input_file : str
        Path to input audio file.

    output_file : str
        Path to output audio file.

    silence_threshold : float
        Silence threshold as percentage of maximum sample value.

    min_voicing_duration : float
        Minimum amout of time required to be considered non-silent.

    Returns
    -------
    status : bool
        True on success.
    """
    args = [input_file, output_file]
    args.append("silence")

    args.append("1")
    args.append("%f" % min_voicing_duration)
    args.append("%f%%" % silence_threshold)

    args.append("-1")
    args.append("%f" % min_voicing_duration)
    args.append("%f%%" % silence_threshold)

    return sox(args)


def split_along_silence(input_file, output_file, min_silence_dur=0.5,
                        sil_pct_thresh=0.01, min_voicing_dur=1):
    """Takes an audio file with silent sections and splits it up into
    seperate, nonsilent files.

    Output file names are named as output_file001.ext, output_file002.ext, ...

    Parameters
    ----------
    input_file : str
        Path to input audio file.

    output_file : str
        Path to output audio file.

    sil_pct_thresh : float
        Silence threshold as percentage of maximum sample value.

    min_voicing_duration : float
        Minimum amout of time required to be considered non-silent.

    min_silence_duration : float
        Minimum amout of time require to be considered silent.

    Returns
    -------
    status : bool
        True on success.
    """
    args = [input_file, output_file]
    args.append("silence")

    args.append("1")
    args.append("%f" % min_voicing_dur)
    args.append("%f%%" % sil_pct_thresh)

    args.append("1")
    args.append("%f" % min_silence_dur)
    args.append("%f%%" % sil_pct_thresh)

    args.append(":")
    args.append("newfile")
    args.append(":")
    args.append("restart")
    return sox(args)


def play_excerpt(input_file, duration=5, use_fade=False,
                 remove_silence=False):
    """Play an excerpt of an audio file.

    Parameters
    ----------
    input_file : str
        Audio file to play.

    duration : float
        Length of excerpt in seconds.

    use_fade : bool
        If true, apply a fade in and fade out.

    remove_silence: bool
        If true, forces entire segment to have sound by removing silence.
    """
    ext = util.fileext(input_file)
    tmp_file = util.temp_file(ext)
    if remove_silence:
        remove_silence(input_file, tmp_file)
    else:
        tmp_file = input_file

    if not use_fade:
        play(tmp_file, end_t=duration)
    else:
        tmp_file2 = util.temp_file(ext)
        fade(tmp_file, tmp_file2, fade_in_time=0.5, fade_out_time=1)
        play(tmp_file2, end_t=duration)


def play(input_file, start_t=0, end_t=None):
    """Play an audio file.
    Specify start/end time to play a particular segment of the audio.

    Parameters
    ----------
    input_file : str
        Audio file to play.

    start_t : float
        Play start time.

    end_t : float
        Play end time.

    Returns
    -------
    status : bool
        True if successful.
    """
    assert_sox()
    assert is_valid_file_format(input_file), "Invalid file format."

    args = ["play"]
    args.append("--norm")
    args.append("--no-show-progress")
    args.append(input_file)
    args.append('trim')
    args.append("%f" % start_t)
    if end_t:
        args.append("=%f" % end_t)

    logging.info("Executing: %s", "".join(args))
    process_handle = subprocess.Popen(args, stderr=subprocess.PIPE)
    status = process_handle.wait()
    logging.info(process_handle.stdout)

    return status == 0


def is_valid_file_format(input_file):
    """Determine if a given file is supported by SoX based on its extension.

    Parameters
    ----------
    input_file : str
        Audio file to verify for support.

    Returns
    -------
    status : bool
        True if supported.
    """

    # File extension
    file_ext = os.path.splitext(input_file)[-1]
    # Return False if the file lacks an extension.
    if not file_ext:
        return False
    # Remove dot-separator.
    file_ext = file_ext.strip(".")
    # Pure wave support
    if file_ext == pywave.WAVE_EXT:
        return True

    # Otherwise, check against SoX.
    else:
        assert_sox()
        status = os.popen('sox -h').readlines()
        for state in status:
            # Find the entry with ASCII audio formats.
            if state.count('AUDIO FILE FORMATS'):
                valid = file_ext in state

        if valid:
            logging.info("SoX supports '%s' files.", file_ext)
        else:
            logging.info("SoX does not support '%s' files.", file_ext)

        return valid


def soxi_parse(key, value):
    """ Helper function for file_info
    """
    ret_value = None
    try:
        if 'Duration' == key:
            ret_value = [x.strip() for x in value.split('=')]
            # parse time into seconds
            hours, minutes, seconds = ret_value[0].split(':')
            secs_duration = float(seconds) + (int(minutes) * 60.) + \
                (int(hours) * 3600.)
            # parse samples
            samples_duration = int(ret_value[1].split(' ')[0])
            # parse sectors
            ret_value = {"seconds": secs_duration, "samples": samples_duration}
        elif key in ['Channels', 'Sample Rate']:
            ret_value = int(value)
        elif key in ['Precision']:
            ret_value = int(value.split('-')[0])
        elif key in ['File Size']:
            ret_value = float(value.strip('k'))
        elif key in ['Bit Rate']:
            ret_value = float(value.strip('M'))
        else:
            ret_value = value
    # TODO(ejhumphrey): This seems like super bad practice.
    except ValueError:
        ret_value = value
    return ret_value


def file_info(input_file):
    """ Get audio file information including file format, bit rate,
        and sample rate.

    Parameters
    ----------
    input_file : str
        Audio file to get information from.

    Returns
    -------
    ret_dict : dictionary
        Dictionary containing file information.
            - Bit Rate
            - Channels
            - Duration
            - File Size
            - Input File
            - Precision
            - Sample Encoding
            - Sample Rate
    """
    if os.path.exists(input_file):
        ret_dict = {}
        soxi_out = subprocess.check_output(["soxi", input_file]).split('\n')
        for line in soxi_out:
            if len(line) > 0:
                separator = line.find(':')
                key = line[:separator].strip()
                value = line[separator+1:].strip()
                ret_dict[key] = soxi_parse(key, value)
        return ret_dict
    else:
        return {}


def file_stats(input_file):
    """ Get audio file information including file format, bit rate,
        and sample rate.

    Parameters
    ----------
    input_file : str
        Audio file to get information from.

    Returns
    -------
    ret_dict : dictionary
        Dictionary containing file statistics.
            - samples read
            - length (seconds)
            - scaled by
            - maximum amplitude
            - minimum amplitude
            - midline amplitude
            - mean norm
            - mean amplitude
            - rms amplitude
            - maximum delta
            - minimum delta
            - mean delta
            - rms delta
            - rough frequency
            - volume adjustment
    """
    # TODO(rabitt): WARNING! This will print a bunch of ugly to ipython.
    # Need to find a way to supress stderr output to the screen while still
    # reading from stderr
    if os.path.exists(input_file):
        ret_dict = {}
        proc = subprocess.check_output(["sox", input_file, "-n", "stat"],
                                       stderr=subprocess.STDOUT).split('\n')
        for line in proc:
            print(line)
            if len(line) > 0:
                separator = line.find(':')
                key = line[:separator].strip().replace(' ', '').lower()
                value = line[separator+1:].strip()
                ret_dict[key] = value
        return ret_dict
    else:
        return {}


def sox(args):
    """Pass an argument list to SoX.

    Parameters
    ----------
    args : list
        Argument list for SoX. The first item can, but does not need to,
        be 'sox'.

    Returns
    -------
    status : bool
        True on success.
    """
    assert_sox()
    if args[0].lower() != "sox":
        args.insert(0, "sox")
    else:
        args[0] = "sox"

    try:
        logging.info("Executing: %s", "".join(args))
        process_handle = subprocess.Popen(args, stderr=subprocess.PIPE)
        status = process_handle.wait()
        logging.info(process_handle.stdout)
        return status == 0
    except OSError as error_msg:
        logging.error("OSError: SoX failed! %s", error_msg)
    except TypeError as error_msg:
        logging.error("TypeError: %s", error_msg)
    return False


def is_pywave(filepath):
    """Determines if Python's wave module can make sense of a given file.

    Note that this is based solely on trying to open the file, and is not
    concerned with the file's extension.

    Returns
    -------
    status: bool
        True on success.
    """
    try:
        pywave.open(filepath, "r")
        return True
    except pywave.Error:
        return False

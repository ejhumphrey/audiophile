"""Heavily refactored pure-Python wave file handling.

Note: Parameter functions have been renamed to harmonize with the audioreader
definition.

Usage:

Reading WAVE files:
      f = wave.open(file, 'r')

where file is either the name of a file or an open file pointer.
The open file pointer must have methods read(), seek(), and close().
When the setpos() and rewind() methods are not used, the seek()
method is not necessary.

Public attributes:
      num_channels       -- number of audio channels (1 for mono, 2 for stereo)
      bytedepth          -- sample width in bytes
      samplerate         -- sampling frequency, in Hertz
      num_frames         -- returns number of audio frames
      comptype           -- compression type ('NONE' for linear samples)
      compname           -- human-readable version of compression type ('not
                            compressed' linear samples)
      params             -- a dict consisting of all of the above
      position           -- return the current position

Public methods:
      read_frames(num)   -- returns at most n frames of audio
      rewind()           -- rewind to the beginning of the audio stream
      set_position(pos)  -- seek to the specified position
      close()            -- close the instance (make it unusable)

The close() method is called automatically when the class instance
is destroyed.

Writing WAVE files:
      f = wave.open(file, 'w', num_channels)
where file is either the name of a file or an open file pointer.
The open file pointer must have methods write(), tell(), seek(), and
close().

Public methods:
      writeframesraw(data)
                      -- write audio frames without pathing up the
                         file header
      writeframes(data)
                      -- write audio frames and patch up the file header
      close()         -- patch up the file header and close the
                         output file

You should set the parameters before the first writeframesraw or
writeframes.  The total number of frames does not need to be set,
but when it is set to the correct value, the header does not have to
be patched up.
It is best to first set all parameters, perhaps possibly the
compression type, and then write audio frames using writeframesraw.
When all frames have been written, either call writeframes('') or
close() to patch up the sizes in the header.
The close() method is called automatically when the class instance
is destroyed.
"""

import __builtin__
import array
import struct
from chunk import Chunk

__all__ = ["open", "openfp", "WaveError", "WAVE_EXT"]

WAVE_EXT = "wav"
WAVE_FORMAT_PCM = 0x0001

_array_fmts = None, 'b', 'h', None, 'l'

if struct.pack("h", 1) == "\000\001":
    big_endian = 1
else:
    big_endian = 0


class WaveError(Exception):
    pass


class Wave_read:
    """Variables used in this class:

    These variables are available to the user though appropriate
    methods of this class:
    _file -- the open file with methods read(), close(), and seek()
              set through the __init__() method
    _nchannels -- the number of audio channels
              available through the getnchannels() method
    _nframes -- the number of audio frames
              available through the getnframes() method
    _sampwidth -- the number of bytes per audio sample
              available through the getsampwidth() method
    _framerate -- the sampling frequency
              available through the getframerate() method
    _comptype -- the AIFF-C compression type ('NONE' if AIFF)
              available through the getcomptype() method
    _compname -- the human-readable AIFF-C compression type
              available through the getcomptype() method
    _soundpos -- the position in the audio stream
              available through the tell() method, set through the
              setpos() method

    These variables are used internally only:
    _fmt_chunk_read -- 1 iff the FMT chunk has been read
    _data_seek_needed -- 1 iff positioned correctly in audio
              file for readframes()
    _data_chunk -- instantiation of a chunk class for the DATA chunk
    _framesize -- size of one frame in the file
    """

    def initfp(self, file):
        self._convert = None
        self._soundpos = 0
        self._file = Chunk(file, bigendian=0)
        if self._file.getname() != 'RIFF':
            raise WaveError('file does not start with RIFF id')
        if self._file.read(4) != 'WAVE':
            raise WaveError('not a WAVE file')
        self._fmt_chunk_read = 0
        self._data_chunk = None
        while 1:
            self._data_seek_needed = 1
            try:
                chunk = Chunk(self._file, bigendian=0)
            except EOFError:
                break
            chunkname = chunk.getname()
            if chunkname == 'fmt ':
                self._read_fmt_chunk(chunk)
                self._fmt_chunk_read = 1
            elif chunkname == 'data':
                if not self._fmt_chunk_read:
                    raise WaveError('data chunk before fmt chunk')
                self._data_chunk = chunk
                self._nframes = chunk.chunksize // self._framesize
                self._data_seek_needed = 0
                break
            chunk.skip()
        if not self._fmt_chunk_read or not self._data_chunk:
            raise WaveError('fmt chunk and/or data chunk missing')

    def __init__(self, f):
        self._i_opened_the_file = None
        if isinstance(f, basestring):
            f = __builtin__.open(f, 'rb')
            self._i_opened_the_file = f
        # else, assume it is an open file object already
        try:
            self.initfp(f)
        except:
            if self._i_opened_the_file:
                f.close()
            raise

    def __del__(self):
        self.close()

    # User visible methods.
    def getfp(self):
        return self._file

    def rewind(self):
        self._data_seek_needed = 1
        self._soundpos = 0

    def close(self):
        if self._i_opened_the_file:
            self._i_opened_the_file.close()
            self._i_opened_the_file = None
        self._file = None

    def tell(self):
        return self._soundpos

    def channels(self):
        return self._nchannels

    def num_samples(self):
        return self._nframes

    def bytedepth(self):
        return self._sampwidth

    def samplerate(self):
        return self._framerate

    def getcomptype(self):
        return self._comptype

    def getcompname(self):
        return self._compname

    def getparams(self):
        return self.getnchannels(), self.getsampwidth(), \
               self.getframerate(), self.getnframes(), \
               self.getcomptype(), self.getcompname()

    def getmarkers(self):
        return None

    def getmark(self, id):
        raise WaveError('no marks')

    def setpos(self, pos):
        if pos < 0 or pos > self._nframes:
            raise WaveError('position not in range')
        self._soundpos = pos
        self._data_seek_needed = 1

    def readframes(self, nframes):
        if self._data_seek_needed:
            self._data_chunk.seek(0, 0)
            pos = self._soundpos * self._framesize
            if pos:
                self._data_chunk.seek(pos, 0)
            self._data_seek_needed = 0
        if nframes == 0:
            return ''
        if self._sampwidth > 1 and big_endian:
            # unfortunately the fromfile() method does not take
            # something that only looks like a file object, so
            # we have to reach into the innards of the chunk object
            chunk = self._data_chunk
            data = array.array(_array_fmts[self._sampwidth])
            nitems = nframes * self._nchannels
            if nitems * self._sampwidth > chunk.chunksize - chunk.size_read:
                nitems = (chunk.chunksize - chunk.size_read) / self._sampwidth
            data.fromfile(chunk.file.file, nitems)
            # "tell" data chunk how much was read
            chunk.size_read = chunk.size_read + nitems * self._sampwidth
            # do the same for the outermost chunk
            chunk = chunk.file
            chunk.size_read = chunk.size_read + nitems * self._sampwidth
            data.byteswap()
            data = data.tostring()
        else:
            data = self._data_chunk.read(nframes * self._framesize)
        if self._convert and data:
            data = self._convert(data)
        self._soundpos = self._soundpos + len(data) \
            // (self._nchannels * self._sampwidth)
        return data

    # Internal methods.
    def _read_fmt_chunk(self, chunk):
        (wFormatTag, self._nchannels, self._framerate, dwAvgBytesPerSec,
            wBlockAlign) = struct.unpack('<hhllh', chunk.read(14))
        if wFormatTag == WAVE_FORMAT_PCM:
            sampwidth = struct.unpack('<h', chunk.read(2))[0]
            self._sampwidth = (sampwidth + 7) // 8
        else:
            raise WaveError('unknown format: %r' % (wFormatTag,))
        self._framesize = self._nchannels * self._sampwidth
        self._comptype = 'NONE'
        self._compname = 'not compressed'


class Wave_write(object):
    """Variables used in this class:

    These variables are user settable through appropriate methods
    of this class:
    _file -- the open file with methods write(), close(), tell(), seek()
              set through the __init__() method
    _comptype -- the AIFF-C compression type ('NONE' in AIFF)
              set through the setcomptype() or setparams() method
    _compname -- the human-readable AIFF-C compression type
              set through the setcomptype() or setparams() method
    _nchannels -- the number of audio channels
              set through the setnchannels() or setparams() method
    _sampwidth -- the number of bytes per audio sample
              set through the setsampwidth() or setparams() method
    _framerate -- the sampling frequency
              set through the setframerate() or setparams() method
    _nframes -- the number of audio frames written to the header
              set through the setnframes() or setparams() method

    These variables are used internally only:
    _datalength -- the size of the audio samples written to the header
    _nframeswritten -- the number of frames actually written
    _datawritten -- the size of the audio samples actually written
    """

    def __init__(self, f):
        self._i_opened_the_file = None
        if isinstance(f, basestring):
            f = __builtin__.open(f, 'wb')
            self._i_opened_the_file = f
        try:
            self.initfp(f)
        except:
            if self._i_opened_the_file:
                f.close()
            raise

    def initfp(self, file):
        self._file = file
        self._convert = None
        self._nchannels = 0
        self._sampwidth = 0
        self._framerate = 0
        self._nframes = 0
        self._nframeswritten = 0
        self._datawritten = 0
        self._datalength = 0

    def __del__(self):
        self.close()

    # User visible methods.
    def set_channels(self, channels):
        if self._datawritten:
            raise WaveError('cannot change parameters after starting to write')
        if channels < 1:
            raise WaveError('bad # of channels')
        self._nchannels = channels

    def channels(self):
        if not self._nchannels:
            raise WaveError('number of channels not set')
        return self._nchannels

    def set_bytedepth(self, bytedepth):
        if self._datawritten:
            raise WaveError('cannot change parameters after starting to write')
        if bytedepth < 1 or bytedepth > 4:
            raise WaveError('bad sample width')
        self._sampwidth = bytedepth

    def bytedepth(self):
        if not self._sampwidth:
            raise WaveError('sample width not set')
        return self._sampwidth

    def set_samplerate(self, samplerate):
        if self._datawritten:
            raise WaveError('cannot change parameters after starting to write')
        if samplerate <= 0:
            raise WaveError('bad frame rate')
        self._framerate = samplerate

    def samplerate(self):
        if not self._framerate:
            raise WaveError('frame rate not set')
        return self._framerate

    def set_num_samples(self, nframes):
        if self._datawritten:
            raise WaveError('cannot change parameters after starting to write')
        self._nframes = nframes

    def num_samples(self):
        return self._nframeswritten

    def setcomptype(self, comptype, compname):
        if self._datawritten:
            raise WaveError('cannot change parameters after starting to write')
        if comptype not in ('NONE',):
            raise WaveError('unsupported compression type')
        self._comptype = comptype
        self._compname = compname

    def getcomptype(self):
        return self._comptype

    def getcompname(self):
        return self._compname

    def setparams(self, params):
        nchannels, sampwidth, framerate, nframes, comptype, compname = params
        if self._datawritten:
            raise WaveError('cannot change parameters after starting to write')
        self.setnchannels(nchannels)
        self.setsampwidth(sampwidth)
        self.setframerate(framerate)
        self.setnframes(nframes)
        self.setcomptype(comptype, compname)

    def getparams(self):
        if not self._nchannels or not self._sampwidth or not self._framerate:
            raise WaveError('not all parameters set')
        return (self._nchannels, self._sampwidth, self._framerate,
                self._nframes, self._comptype, self._compname)

    def setmark(self, id, pos, name):
        raise WaveError('setmark() not supported')

    def getmark(self, id):
        raise WaveError('no marks')

    def getmarkers(self):
        return None

    def tell(self):
        return self._nframeswritten

    def writeframesraw(self, data):
        self._ensure_header_written(len(data))
        nframes = len(data) // (self._sampwidth * self._nchannels)
        if self._convert:
            data = self._convert(data)
        if self._sampwidth > 1 and big_endian:
            import array
            data = array.array(_array_fmts[self._sampwidth], data)
            data.byteswap()
            data.tofile(self._file)
            self._datawritten = self._datawritten + len(data) * self._sampwidth
        else:
            self._file.write(data)
            self._datawritten = self._datawritten + len(data)
        self._nframeswritten = self._nframeswritten + nframes

    def writeframes(self, data):
        self.writeframesraw(data)
        if self._datalength != self._datawritten:
            self._patchheader()

    def close(self):
        if self._file:
            self._ensure_header_written(0)
            if self._datalength != self._datawritten:
                self._patchheader()
            self._file.flush()
            self._file = None
        if self._i_opened_the_file:
            self._i_opened_the_file.close()
            self._i_opened_the_file = None

    # Internal methods.
    def _ensure_header_written(self, datasize):
        if not self._datawritten:
            if not self._nchannels:
                raise WaveError('# channels not specified')
            if not self._sampwidth:
                raise WaveError('sample width not specified')
            if not self._framerate:
                raise WaveError('sampling rate not specified')
            self._write_header(datasize)

    def _write_header(self, initlength):
        self._file.write('RIFF')
        if not self._nframes:
            self._nframes = initlength / (self._nchannels * self._sampwidth)
        self._datalength = self._nframes * self._nchannels * self._sampwidth
        self._form_length_pos = self._file.tell()
        self._file.write(
            struct.pack(
                '<l4s4slhhllhh4s',
                36 + self._datalength, 'WAVE', 'fmt ', 16,
                WAVE_FORMAT_PCM, self._nchannels, self._framerate,
                self._nchannels * self._framerate * self._sampwidth,
                self._nchannels * self._sampwidth,
                self._sampwidth * 8, 'data'))
        self._data_length_pos = self._file.tell()
        self._file.write(struct.pack('<l', self._datalength))

    def _patchheader(self):
        if self._datawritten == self._datalength:
            return
        curpos = self._file.tell()
        self._file.seek(self._form_length_pos, 0)
        self._file.write(struct.pack('<l', 36 + self._datawritten))
        self._file.seek(self._data_length_pos, 0)
        self._file.write(struct.pack('<l', self._datawritten))
        self._file.seek(curpos, 0)
        self._datalength = self._datawritten


def open(f, mode=None):
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        return Wave_read(f)
    elif mode in ('w', 'wb'):
        return Wave_write(f)
    else:
        raise WaveError("mode must be 'r', 'rb', 'w', or 'wb'")

openfp = open  # B/W compatibility

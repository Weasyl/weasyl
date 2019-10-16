import itertools
import lzma
import struct
import os
import zlib

from libweasyl.compat import iterbytes


def iter_decompressed_zlib(fobj, chunksize=1024):
    """
    An iterator over the decompressed bytes of a zlib-compressed file object.

    Args:
        fobj: The input file object. The file can be at any position, as long
            as the current position is the start of the zlib stream.
        chunksize (int): The number of bytes to read from the file at a time.

    Returns:
        iterator: An iterator yielding each byte as it's decompressed from the
            file object.
    """
    decompressor = zlib.decompressobj()
    while True:
        chunk = fobj.read(chunksize)
        if not chunk:
            for b in iterbytes(decompressor.flush()):
                yield b
            break
        for b in iterbytes(decompressor.decompress(chunk)):
            yield b


SIZES = 'xmin', 'xmax', 'ymin', 'ymax'
SIGNATURE_COMPRESSION = {
    b'FWS': None,
    b'CWS': 'zlib',
    b'ZWS': 'lzma',
}


def parse_flash_header(fobj):
    """
    Parse (parts of) the header of a flash object.

    The following information will be parsed out of the flash object:

    ``compression``
      A value indicating the compression format used. This can be either
      :py:data:`None`, the string ``'zlib'``, or the string ``'lzma'``.

    ``version``
      The file version number.

    ``size``
      The decompressed (if applicable) size of the file.

    ``width``, ``height``
      The size of the on-screen display.

    Args:
        fobj: The input file object. Will not be closed.

    Returns:
        dict: A dict containing the following keys: ``compression``,
            ``version``, ``size``, ``width``, ``height``.
    """
    signature = fobj.read(3)
    if signature not in SIGNATURE_COMPRESSION:
        raise ValueError('not a SWF file')

    ret = {}
    ret['compression'] = SIGNATURE_COMPRESSION[signature]
    ret['version'] = ord(fobj.read(1))
    ret['size'], = struct.unpack(b'<I', fobj.read(4))

    if ret['compression'] == 'zlib':
        stream = iter_decompressed_zlib(fobj)
    elif ret['compression'] == 'lzma':
        fobj.seek(5, os.SEEK_CUR)
        dict_size, = struct.unpack(b'<I', fobj.read(4))
        filters = [{
            'id': lzma.FILTER_LZMA1,
            'dict_size': dict_size,
        }]
        lzma_fobj = lzma.LZMAFile(
            fobj, 'rb', format=lzma.FORMAT_RAW, filters=filters)
        stream = iter(lambda: lzma_fobj.read(1), b'')
    else:
        stream = iter(lambda: fobj.read(1), b'')

    first_byte = ord(next(stream))
    bits_per_value = first_byte >> 3
    mask = (1 << bits_per_value) - 1
    nbits = 5 + bits_per_value * len(SIZES)
    bytes_to_read = (nbits + 7) // 8 - 1
    value_buffer = first_byte & 0b111
    for byte in itertools.islice(stream, bytes_to_read):
        value_buffer = (value_buffer << 8) | ord(byte)
    stray_bits = 8 - nbits % 8
    if stray_bits != 8:
        value_buffer >>= stray_bits
    bbox = {}
    for name in reversed(SIZES):
        bbox[name] = (value_buffer & mask) / 20
        value_buffer >>= bits_per_value

    if bbox['xmin'] != 0 or bbox['ymin'] != 0:
        raise ValueError('invalid SWF file')
    ret['width'] = bbox['xmax']
    ret['height'] = bbox['ymax']

    return ret

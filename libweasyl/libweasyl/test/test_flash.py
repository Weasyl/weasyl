from __future__ import unicode_literals

import base64
from io import BytesIO

from libweasyl.test.common import datadir
from libweasyl import flash


compressed_data = base64.b64decode("""
eJztwYs3FQYAwGGRWtNVijpdbC4uK9uELpJQOnlUmsNQasLConJD6TFaZElUNkcdRdGLClntHGWT
ig6ux9ULZeW68w6ZjpLH/pHf96moAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AACgolIvvdum19ggX/y3dZpGfLLSM3TbaPaYhueUnu3JiFc77+WEWy3LneMm6J1IsQoxSwhST2p/
kJ0WIBQYpH+YEtpqSfJcYqx0ph7bbFa0HRgoMTTdYLl13kG/3o4RnVL5A+WhwFuZDr6SxApZxZnV
w4fa5HHOctnRZsVyf4uIm1Vt+lFHxzo9vQr2GcePv+gXxA4Hf7Gv2a3942iQWvKsubMWyCJdTxho
SO3375etkke193llhn2zuXFet+hcb05eQPD9n7wPhydn//6v9MAvTqU+cpOGVcKzGrsOvqz0jd51
49Ylk+6whqDSUyOxxUmW/eUSu0WzV44rns43t3e40Xsuw+zd1dxdJW4xAvEGjZuTVX5/pZo9fzUV
4iI2Fjyr+6pEXrtlfK5gcv2HAMURY6mz7hl5Ymqe/bGtGZmywtQWn9Mri4vuCCuH9yTtdq88ahHV
E+cldGyt6kmWj5T8OqHsLNNN+GBo0BTeXCVOry51vGPslWB7ePX1vdEdDdneYvVI8YEI/ZOGw/vW
1mS3WtqPxK7LCkwfWpRhelkmCYj40yctymwy/mTN9isnGwz75b4PLazENZeqjfw8+5S7R92KrN6a
T0YtWKg55FudNaHe4mNjV1Z8fKKr8qqv9VKr2Q26R+Q/f/mjUeHMmu2SSkOx53ET2ZDJ84FG708K
WYW6v9fk/YHXRRZLHykVP4z4TQmPhMX+Ji5dY7rDP/+JQurwPtAlucI0bUbWlaThlKKPj03feJld
63TuyzovMtFv6phhp2tzIfqe0efNJhEFAeJ7c779zLf1/Tt514JjLul3VV1yPFbXr5Bej3dXtEhr
JCMFXrsvu9gknh20+zrr8JV684bQOJMl128UT+tabC0Ys9/bOV/cmNg1mV+eEXpKZ5lxrkKu17Ep
alKzTL/k9aiq+6vhXuvBcK2c4LVuPafrb5+X6N/22DPuv9zyRJzhC9fUmOC7aY/3ay928FiROqq5
ZKjHYEl236Ceo8p3j5zySx/quHbfsK13105W25YYXhftUygKTe3fOtDuGFx3pm9ut77Wu9tNLk1D
j5o/Ob28mKRtNvXfWG/tjLAL9q3jketziw2/FIVO867sfX9IaL7TSTBzfrlVTeCw5cN6X90W4+iD
kRVvzRVKb+/MApWEtRuDV605VztVXrdDbctV/XkRHoPWWspGuV7XG811/6hLTceMM426g7JPt03k
J3dGj0ULdK6VJRjFGGkZXlpYUB+Y8lGzazT5rNJIXbTE3ktiOeRcLYl4LLX0LQjbeG2FSJZ/qKWr
KuVDUOW0i67T1S6bfO/e0aWqfHOwR5TT8WzphkHzufbb8kL0VEqnP839Y2RbxI78PFHBmTof73dt
3aVbLMue3N+kHWwtFHY61/YXvp91M8VVVTtk7OX/1oEGYQ==
""")


decompressed_data = base64.b64decode("""
znG63RzQz9EpvjaOC3+J5FFnYPee+gtR/xw4j2zcbbufazM0og9JDer9izNmK4NiBYbhwp6OXxoN
IJL4/xo4ETWjR3UzFf/HN1ri3XrusiInTTJdEntY6uP0FbnRwuR8YbGXPlc1hMHMwZhC8nzd0X5D
0cyF2OI5WzFsrcbdHXOF+uZRU6p3JH/81+wNePJjHnfYSeH592IDiQkQCRbMcEiMIAtxPHl5zEHR
c+HrU5doLVrQEughnOqfo19jwGlUgGuJnpTlcXqBQLlW0SbPQRqZC25728VXdG6ssaQm6GjPYrmQ
9HiwhjLsvzU6GQw9/OLUEy88PqzqnJUr8aeibrJJdQ0lTQut/sZYvY0r1tz/ZkclJA3VzSiy0ctc
/BAN/kz4X+KCJHFDG5jRhI2jPIhdlZfMro3ZVpE9sK+1GsXycoZvSsWFMXPpflMaP9rG6YnR9LKH
/eTmvBuD+CIg0mvYxiWSybk/tSRTgziAQqt2dOPPnlQlBXAlemwdjyLyd0bKntoyPPR4S5thkvAZ
lSelzDVfbLZWjnMr/n+PymWmj88i7NFXwzEzJcqkySNYUevkb/dJrzPtL/5zFhcO8FfJm/0F2VY3
Orywiv3nxadXNjAzDM8bgtF9H2QjrgfKZTXFIiVRiibM8CbW7tBU++LMwQVbU/7A7t+vMTDE5OJe
9Fj/GoJoeJMluUQnalup0+JxPvVhR4nBJ44Gm6aG8ouv+ccn4FMrqOZD65udISYd0uMGOhs3oHS7
IwrYJmyqXyW7Dy4IV9r18dHnFohHkroCR59OQs47cat/SuLZcco19KpTb6VHN4SZ7zosm4Cmzi/P
Z34mKqussAHnKTYN+jx25hMl0ITn/qm/lWeQFTQkouLRHONZc/4OvB2y3/cCStzy6jbvaxGfY0ZJ
6ZHOtJ01HbROcvxbOTKMfiLXSI11Y7qOx3kUKT5OO433Dirw6SAqnuvvHD8AUMRAqbnDFUjorDjO
ShSJA2CEa810Vq4hZ43sXe7hP2PNmOsQ6B0R8bTSR9LwxNj7QNuhhhQr//P66ssGaKA82vxwTKKw
Ih8hZwFUxer1fBovbUANBxO/M8ph8jLDzlcb2SR0e3DB7S/i5FRUl6oAg0ZPY0FEnMv/v81qA1yn
HRJsTu82EeTQ0Rzn4A5L3gVxJ/oklyPoYp6R3f2pieZ0+nQNFai8gyN1IxEipBeqzmGL+Q7n94mZ
5CMFISo8UzUy8EPJNWzHcTJXqmhPqDshzKl82efGi/hixQGhSAQDpSZVSuPnAuTge+khn+PVME3v
LxA8YKNmHAC5BNSis/RgbGqpoyGqmM1WVPHd6LlcMrzTwFkUYzYaGuZDy+yu9Qmti0gCFGb62w==
""")


def test_iter_decompressed_zlib_lazily_reads_chunks():
    """
    iter_decompressed_zlib reads chunks at a time; it will not read the entire
    file at once if it doesn't need to.
    """
    fobj = BytesIO(compressed_data)
    it = flash.iter_decompressed_zlib(fobj)
    next(it)
    assert fobj.tell() not in {0, len(compressed_data)}


def test_iter_decompressed_zlib_reads_by_chunksize():
    """
    iter_decompressed_zlib will read from the provided file object in
    increments of chunksize.
    """
    fobj = BytesIO(compressed_data)
    it = flash.iter_decompressed_zlib(fobj, chunksize=99)
    next(it)
    assert fobj.tell() == 99


def test_iter_decompressed_zlib_can_read_all_bytes():
    """
    iter_decompressed_zlib will eventually read all of the bytes in the
    provided file object.
    """
    fobj = BytesIO(compressed_data)
    it = flash.iter_decompressed_zlib(fobj)
    assert bytes(it) == b'\0' * 65536 + decompressed_data


def test_read_uncompressed_flash_header():
    """
    parse_flash_header can parse the header of uncompressed flash files.
    """
    infile = datadir.join('test.swf').open(mode='rb')
    header = flash.parse_flash_header(infile)
    assert header == {
        'compression': None,
        'size': 153,
        'version': 5,
        'width': 550,
        'height': 400,
    }


def test_read_zlib_compressed_flash_header():
    """
    parse_flash_header can parse the header of zlib compressed flash files.
    """
    infile = datadir.join('flash_eyes.swf').open(mode='rb')
    header = flash.parse_flash_header(infile)
    assert header == {
        'compression': 'zlib',
        'size': 15900,
        'version': 6,
        'width': 300,
        'height': 300,
    }


def test_read_lzma_compressed_flash_header():
    """
    parse_flash_header can parse the header of lzma compressed flash files.
    """
    infile = datadir.join('lzma.swf').open(mode='rb')
    header = flash.parse_flash_header(infile)
    assert header == {
        'compression': 'lzma',
        'size': 3294,
        'version': 25,
        'width': 550,
        'height': 400,
    }

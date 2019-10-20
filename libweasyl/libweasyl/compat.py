import sys


_PY3 = sys.version_info >= (3, 0)


if _PY3:
    str = str

    def iterbytes(b):
        for e in range(len(b)):
            yield b[e:e + 1]
else:
    str = str
    iterbytes = iter


__all__ = ['_PY3', 'iterbytes', 'str']

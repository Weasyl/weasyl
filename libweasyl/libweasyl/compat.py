import sys


if sys.version_info < (3, 0):
    _PY3 = False
else:
    _PY3 = True


if _PY3:
    unicode = str
    def iterbytes(b):
        for e in range(len(b)):
            yield b[e:e + 1]
else:
    unicode = unicode
    iterbytes = iter


__all__ = ['_PY3', 'iterbytes', 'unicode']

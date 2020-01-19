# encoding: utf-8

"""
Image manipulation with Pillow.
"""
from io import BytesIO, IOBase
from math import ceil
from PIL import Image, ImageSequence

from copy import deepcopy

COVER_SIZE = 1024, 3000
"The maximum size of a cover image, in pixels."

THUMB_HEIGHT = 250
"The maximum height of a thumbnail, in pixels."


def gif_to_frames(image):
    frames = ImageSequence.Iterator(image)
    for frame in frames:
        yield frame.copy()


class WeasylImage(object):

    def __init__(self, fp=None, string=None):
        self._file_format = None
        self._frames = []
        self.webp = None
        self._size = (0, 0)
        self.is_animated = False
        self._info = None
        self.duration = []
        if string:
            with BytesIO(string) as in_file:
                self._load(in_file)
        elif fp:
            if isinstance(fp, str):
                with open(fp, 'rb') as in_file:
                    self._load(in_file)
            elif isinstance(fp, IOBase) or isinstance(fp, file):
                self._load(fp)
            else:
                raise IOError
        else:
            raise IOError

    def _load(self, in_file):
        """
        Loads our image.
        All frames are copied to memory, as if we don't Pillow gets upset when the input file is closed.

        If the image is a GIF, this handles converting the GIF from tiled mode, as well as any pallet nonsense.
        Frame duration is also copied, as that needs to be provided at save time.

        :param in_file:
        :return:
        """
        image = Image.open(in_file)
        self._file_format = image.format
        self._size = image.size
        self._info = image.info
        self.is_animated = getattr(image, 'is_animated', False)
        if self.is_animated:
            pallet = image.getpalette()
            mode = image.mode
            tile = 'full'
            while True:
                new_frame = Image.new(mode, image.size)
                if mode == 'P':
                    if not image.getpalette():
                        new_frame.putpalette(pallet)
                    else:
                        new_frame.putpalette(image.getpalette())
                try:
                    if image.tile:
                        tile = image.tile[0]
                        update_region = tile[1]
                        update_region_dimensions = update_region[2:]
                        if update_region_dimensions != image.size:
                            tile = 'partial'
                    if tile == 'partial':
                        new_frame.paste(self._frames[-1])
                    new_frame.paste(image)
                    self._frames.append(new_frame)
                    self.duration.append(image.info['duration'])
                    image.seek(image.tell()+1)
                except EOFError:
                    break
        else:
            self._frames.append(image.copy())

    @property
    def attributes(self):
        return {'width': self._size[0], 'height': self._size[1]}

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        raise AttributeError('Use resize to change size')

    @property
    def file_format(self):
        if self._file_format == "JPEG":
            return "jpg"
        else:
            return self._file_format.lower()

    @property
    def image_extension(self):
        return ".{}".format(self.file_format)

    @property
    def frames(self):
        return len(self._frames)

    def _write(self, out, *args, **kwargs):
        if 'format' not in kwargs:
            kwargs['format'] = self._file_format
        if kwargs['format'].lower() == 'jpg':
            kwargs['format'] = 'jpeg'
        if self.is_animated:
            kwargs['save_all'] = True
            kwargs['append_images'] = self._frames[1:]
            kwargs['duration'] = self.duration
            kwargs['optimize'] = True
            kwargs['loop'] = 0
        self._frames[0].save(out, *args, **kwargs)

    def to_buffer(self, *args, **kwargs):
        with BytesIO() as image_bytes:
            self._write(image_bytes, *args, **kwargs)
            return image_bytes.getvalue()

    def save(self, fp, *args, **kwargs):
        self._write(fp, *args, **kwargs)

    def resize(self, size):
        """
        Resize the image if necessary. Will not resize images that fit entirely
        within target dimensions.

        Parameters:
            size: Tuple (width, height)
        """
        if self._size[0] > size[0] or self._size[1] > size[1]:
            for i in range(0, len(self._frames)):
                self._frames[i] = self._frames[i].resize(size)
            self._size = self._frames[0].size

    def crop(self, bounds):
        """
        Crops the image using the bounds provided
        :param bounds: tuple of ( left, upper, right, lower)
        :return: None
        """
        for i in range(0, len(self._frames)):
            self._frames[i] = self._frames[i].crop(bounds)
        self._size = self._frames[0].size

    def shrink(self, size):
        """

        :param size:
        :return:
        """
        ratio = min(size[0] / float(self._size[0]), size[1] / float(self._size[1]))
        shrunk_size = (int(ceil(self._size[0] * ratio)), int(ceil(self._size[1] * ratio)))
        if self._size != shrunk_size:
            self.resize(shrunk_size)

    def shrinkcrop(self, size, bounds=None):
        """

        :param size: tuple of (width, height)
        :param bounds: tuple of (left, upper, right, lower)
        :return: None
        """
        if bounds:
            if bounds[0:2] != (0, 0) or bounds[2:4] != self._size:
                self.crop(bounds)
            if self._size != size:
                self.resize(size)
            return
        elif self._size == size:
            return

        actual_aspect = self._size[0]/float(self._size[1])
        ideal_aspect = size[0] / float(size[1])
        print(actual_aspect, ideal_aspect)
        if actual_aspect > ideal_aspect:
            new_width = int(ideal_aspect * self._size[1])
            offset = (self.size[0] - new_width) / 2
            resize = (offset, 0, self._size[0] - offset, self._size[1])
        else:
            new_height = int(self._size[0] / ideal_aspect)
            offset = (self._size[1] - new_height) / 2
            resize = (0, offset, self._size[0], self._size[1] - offset)
        self.crop(resize)

        self.shrink(size)

    def get_thumbnail(self, bounds=None):
        image = self._frames[0]
        self._frames = self._frames[:1]
        if image.mode in ('1', 'L', 'LA', 'I', 'P'):
            image = image.convert(mode='RGBA' if image.mode == 'LA' or 'transparency' in image.info else 'RGB')

        if bounds is None:
            source_rect, result_size = get_thumbnail_spec(image.size, THUMB_HEIGHT)
        else:
            source_rect, result_size = get_thumbnail_spec_cropped(
                _fit_inside(bounds, image.size),
                THUMB_HEIGHT)
        if source_rect == (0, 0, image.width, image.height):
            image.draft(None, result_size)
            image = image.resize(result_size, resample=Image.LANCZOS)
        else:
            # TODO: draft and adjust rectangle?
            image = image.resize(result_size, resample=Image.LANCZOS, box=source_rect)

        if self._file_format == 'JPEG':
            out = self.to_buffer(format='JPEG', quality=95, optimize=True, progressive=True, subsampling='4:2:2')
            compatible = (out, 'JPG')

            lossless = False
        elif self._file_format in ('PNG', 'GIF'):
            out = self.to_buffer(format='PNG', optimize=True)
            compatible = (out, 'PNG')

            lossless = True
        else:
            raise Exception("Unexpected image format: %r" % (self._file_format,))

        out = self.to_buffer(format='WebP', lossless=lossless, quality=100 if lossless else 90, method=6)
        webp = (out, 'WEBP')

        if not len(webp[0]) >= len(compatible[0]):
            self.webp = webp[0]

        self._file_format = compatible[1]
        self._size = image.size

    def copy(self):
        """
        Creates a deep copy of the image class
        :return: WeasylImage()
        """
        return deepcopy(self)

    def __str__(self):
        return "WeasylImage: Size {}, File Type: {}, Animated: {}".format(self.size, self.file_format, self.is_animated)

def get_thumbnail_spec(size, height):
    """
    Get the source rectangle (x, y, x + w, y + h) and result size (w, h) for
    the thumbnail of the specified height of an image with the specified size.
    """
    size_width, size_height = size

    max_source_width = 2 * max(size_height, height)
    max_source_height = max(2 * size_width, height)

    source_width = min(size_width, max_source_width)
    source_height = min(size_height, max_source_height)
    source_left = (size_width - source_width) // 2
    source_top = 0

    result_height = min(size_height, height)
    result_width = (source_width * result_height + source_height // 2) // source_height

    return (
        (source_left, source_top, source_left + source_width, source_top + source_height),
        (result_width, result_height),
    )


def get_thumbnail_spec_cropped(rect, height):
    """
    Get the source rectangle and result size for the thumbnail of the specified
    height of a specified rectangular section of an image.
    """
    left, top, right, bottom = rect
    inner_rect, result_size = get_thumbnail_spec((right - left, bottom - top), height)
    inner_left, inner_top, inner_right, inner_bottom = inner_rect

    return (inner_left + left, inner_top + top, inner_right + left, inner_bottom + top), result_size


def _fit_inside(rect, size):
    left, top, right, bottom = rect
    width, height = size

    return (
        max(0, left),
        max(0, top),
        min(width, right),
        min(height, bottom),
    )


def check_crop(dim, x1, y1, x2, y2):
    """
    Return True if the specified crop coordinates are valid, else False.
    """
    return (
            x1 >= 0 and y1 >= 0 and x2 >= 0 and y2 >= 0 and x1 <= dim[0] and
            y1 <= dim[1] and x2 <= dim[0] and y2 <= dim[1] and x2 > x1 and y2 > y1)

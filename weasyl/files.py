import os
import codecs

from libweasyl.constants import Category
from libweasyl.exceptions import InvalidFileFormat, UnknownFileFormat
from libweasyl.files import file_type_for_category
from weasyl.error import WeasylError
import weasyl.define as d
import weasyl.macro as m


def read(filename):
    with codecs.open(filename, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def ensure_file_directory(filename):
    dirname = os.path.dirname(filename)
    os.makedirs(dirname, exist_ok=True)


def append(filename, content):
    """
    Appends text to the specified file.
    """
    with codecs.open(filename, "a", "utf-8") as f:
        f.write(content)


def make_character_directory(target):
    path = d.get_character_directory(target)
    os.makedirs(path, exist_ok=True)


def make_resource(userid, target, feature, *, file_type=None):
    """
    Returns the full path to the specified resource.
    """
    root = d.get_character_directory(target)

    if feature == "char/submit":
        filename = "%d.submit.%d.%s" % (target, userid, file_type)
    elif feature == "char/cover":
        filename = "%d.cover.%s" % (target, file_type)
    elif feature == "char/thumb":
        filename = "%d.thumb.%s" % (target, file_type)
    elif feature == "char/.thumb":
        filename = "%d.new.thumb" % (target,)
    else:
        raise ValueError("Unknown character resource %r" % (feature,))

    return os.path.join(root, filename)


_feature_typeflags = {
    "submit": "=",
    "cover": "~",
}

FILE_TYPE_FLAGS = {
    "jpg": "J",
    "png": "P",
    "gif": "G",
    "webp": "W",
}


def typeflag(feature, file_type):
    symbol = _feature_typeflags[feature]
    letter = FILE_TYPE_FLAGS[file_type]
    return symbol + letter


_categories = {
    m.TEXT_SUBMISSION_CATEGORY: Category.literary,
    m.MULTIMEDIA_SUBMISSION_CATEGORY: Category.multimedia,
}


def get_extension_for_category(filedata, category):
    try:
        _, fmt = file_type_for_category(filedata, _categories[category])
    except UnknownFileFormat as uff:
        e = WeasylError('FileType')
        e.error_suffix = uff.args[0]
        raise e
    except InvalidFileFormat as iff:
        e = WeasylError('FileType')
        e.error_suffix = iff.args[0]
        raise e
    else:
        return '.' + fmt

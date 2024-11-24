import os
import glob
import errno
import codecs
import shutil

from libweasyl.constants import Category
from libweasyl.exceptions import InvalidFileFormat, UnknownFileFormat
from libweasyl.files import file_type_for_category
from libweasyl import security
from weasyl.error import WeasylError
import weasyl.define as d
import weasyl.macro as m


def read(filename):
    with codecs.open(filename, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def ensure_file_directory(filename):
    dirname = os.path.dirname(filename)
    os.makedirs(dirname, exist_ok=True)


def write(filename, content):
    """
    Writes bytes to the specified file.
    """
    ensure_file_directory(filename)

    with open(filename, "wb") as f:
        f.write(content)


def append(filename, content):
    """
    Appends text to the specified file.
    """
    with codecs.open(filename, "a", "utf-8") as f:
        f.write(content)


# Copy the specified file.
copy = shutil.copy


def _remove_glob(glob_path):
    """
    Removes files matching the specified pattern.
    """
    for f in glob.glob(glob_path):
        try:
            os.remove(f)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


def get_temporary(userid, feature):
    """
    Return the full pathname to a temporary file.
    Temporary files are named so as to be owned by a user.
    """
    return "{temp}{userid}.{feature}.{random}".format(temp=m.MACRO_SYS_TEMP_PATH, userid=userid,
                                                      feature=feature, random=security.generate_key(20))


def clear_temporary(userid):
    """
    Remove temporary files owned by a user.
    """
    _remove_glob("{temp}{userid}.*".format(temp=m.MACRO_SYS_TEMP_PATH, userid=userid))


def make_character_directory(target):
    path = d.get_character_directory(target)
    os.makedirs(path, exist_ok=True)


def make_resource(userid, target, feature, extension=None):
    """
    Returns the full path to the specified resource.
    """
    root = d.get_character_directory(target)

    if feature == "char/submit":
        filename = "%d.submit.%d%s" % (target, userid, extension)
    elif feature == "char/cover":
        filename = "%d.cover%s" % (target, extension)
    elif feature == "char/thumb":
        filename = "%d.thumb%s" % (target, extension)
    elif feature == "char/.thumb":
        filename = "%d.new.thumb" % (target,)
    else:
        raise ValueError("Unknown character resource %r" % (feature,))

    return os.path.join(root, filename)


_feature_typeflags = {
    "submit": "=",
    "cover": "~",
}

_extension_typeflags = {
    ".jpg": "J",
    ".png": "P",
    ".gif": "G",
}


def typeflag(feature, extension):
    symbol = _feature_typeflags[feature]
    letter = _extension_typeflags[extension]
    return symbol + letter


_categories = {
    m.ART_SUBMISSION_CATEGORY: Category.visual,
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

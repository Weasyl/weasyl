# files.py

from __future__ import absolute_import

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


PATH_ROOT = os.environ['WEASYL_ROOT'] + '/'

PATH_LOG = "log/"
PATH_SAVE = "save/"
PATH_TEMP = "temp/"
PATH_CONFIG = "config/"
PATH_SEARCH = "search/"


def read(filename, encoding="utf-8", errors="replace", encode=None):
    """
    Returns file data. If the filename is invalid, None is returned.
    """
    try:
        data = codecs.open(filename, "r", encoding, errors).read()
    except IOError:
        d.log_exc()
        return None

    if encode:
        return data.encode(encode)
    else:
        return data


def ensure_file_directory(filename):
    dirname = os.path.dirname(filename)
    try:
        os.stat(dirname)
    except OSError as e:
        if e.errno == errno.ENOENT:
            os.makedirs(dirname)


def write(filename, content, encoding="utf-8", decode=False):
    """
    Writes content to the specified file. If the content comes from a readable
    uploaded text file, set decode to True, else if it comes from a text input,
    use the defaults. If the content comes from an uploaded image file, set
    encoding to None.
    """
    if decode and type(content) is str:
        content = content.decode("raw_unicode_escape")

    ensure_file_directory(filename)

    if encoding:
        with codecs.open(filename, "w", encoding) as fio:
            fio.write(content)
    else:
        with open(filename, "wb") as fio:
            fio.write(content)


def easyupload(filename, content, feature):
    if feature == "text":
        write(filename, content, decode=True)
    elif feature == "image":
        write(filename, content, encoding=None)
    elif feature == "file":
        write(filename, content, encoding=None)
    else:
        raise ValueError


def append(filename, content, encoding="utf-8", decode=False, formfeed=False):
    """
    Appends content to the specified file. If the content comes from a readable
    uploaded text file, set decode to True, else use the defaults. Set
    formfeed to append a formfeed character before the content.
    """
    if decode and type(content) is str:
        content = content.decode("raw_unicode_escape")

    try:
        if encoding:
            with codecs.open(filename, "a", encoding) as fio:
                if formfeed:
                    fio.write("\n")

                fio.write(content)
        else:
            with open(filename, "a") as fio:
                if formfeed:
                    fio.write("\n")

                fio.write(content)
    except IOError:
        return False
    else:
        return True

# Copy the specified file.
copy = shutil.copy


def remove(glob_path):
    """
    Removes the specified file.
    """
    if not glob_path:
        return
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

    return "{root}{temp}{userid}.{feature}.{random}".format(root=PATH_ROOT, temp=PATH_TEMP, userid=userid,
                                                            feature=feature, random=security.generate_key(20))


def clear_temporary(userid):
    """
    Remove temporary files owned by a user.
    """

    remove("{root}{temp}{userid}.*".format(root=PATH_ROOT, temp=PATH_TEMP, userid=userid))


def makedirs(path):
    """
    Make the full hash path to a resource directory on the file system.
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def make_path(target, root):
    path = d.get_hash_path(target, root)
    makedirs(path)


def make_resource(userid, target, feature, extension=None):
    """
    Returns the full path to the specified resource.
    """
    # Character
    if feature == "char/submit":
        return "%s%d.submit.%d%s" % (d.get_hash_path(target, "char"), target, userid, extension)
    if feature == "char/cover":
        return "%s%d.cover%s" % (d.get_hash_path(target, "char"), target, extension)
    if feature == "char/thumb":
        return "%s%d.thumb%s" % (d.get_hash_path(target, "char"), target, extension)
    if feature == "char/.thumb":
        return "%s%d.new.thumb" % (d.get_hash_path(target, "char"), target)
    # Journal
    if feature == "journal/submit":
        return "%s%d.txt" % (d.get_hash_path(target, "journal"), target)
    # Unknown
    raise ValueError

feature_typeflags = {
    "thumb": "-",
    "cover": "~",
    "avatar": ">",
    "banner": "<",
    "propic": "#"
}

extension_typeflags = {
    ".jpg": "J",
    ".png": "P",
    ".gif": "G",
    ".txt": "T",
    ".htm": "H",
    ".mp3": "M",
    ".swf": "F",
    ".pdf": "A"
}


def typeflag(feature, extension):
    symbol = feature_typeflags.get(feature, "=")
    letter = extension_typeflags.get(extension)
    return symbol + letter if letter else ""


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

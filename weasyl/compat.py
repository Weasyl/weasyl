from __future__ import absolute_import

import posixpath


# TODO: Delete this. Use the real request. Need to replace 'path_for' in templates.
class FakePyramidRequest(object):
    def resource_path(self, rsrc, *parts):
        if rsrc is not None:
            raise NotImplementedError("can't do resource_path for non-None resources", rsrc)
        return '/' + posixpath.join(*parts)

    def path_for(self, obj, *a, **kw):
        return obj.canonical_path(self, *a, **kw)

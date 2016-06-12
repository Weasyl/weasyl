import re
import inspect
import posixpath

from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx import addnodes
from sphinx.ext.autosummary import Autosummary, autosummary_toc, get_import_prefixes_from_env, import_by_name


class Autoautosummary(Autosummary):
    option_spec = Autosummary.option_spec.copy()
    option_spec['automembers'] = directives.flag

    def run(self):
        self.env = env = self.state.document.settings.env
        self.genopt = {}
        self.warnings = []
        self.result = ViewList()

        names = [x.strip().split()[0] for x in self.content
                 if x.strip() and re.search(r'^[~a-zA-Z_]', x.strip()[0])]
        if 'automembers' in self.options:
            names.extend(self.find_automembers())
        items = self.get_items(names)
        nodes = self.get_table(items)

        if 'toctree' in self.options:
            dirname = posixpath.dirname(env.docname)

            tree_prefix = self.options['toctree'].strip()
            docnames = []
            for name, sig, summary, real_name in items:
                docname = posixpath.join(tree_prefix, real_name)
                docname = posixpath.normpath(posixpath.join(dirname, docname))
                if docname not in env.found_docs:
                    self.warn('toctree references unknown document %r'
                              % docname)
                docnames.append(docname)

            tocnode = addnodes.toctree()
            tocnode['includefiles'] = docnames
            tocnode['entries'] = [(None, docname) for docname in docnames]
            tocnode['maxdepth'] = -1
            tocnode['glob'] = None

            tocnode = autosummary_toc('', '', tocnode)
            nodes.append(tocnode)

        return self.warnings + nodes

    def find_automembers(self):
        env = self.state.document.settings.env
        prefixes = get_import_prefixes_from_env(env)
        objects = [import_by_name(p) for p in prefixes if p is not None]
        new_names = []
        for name, obj, _, _ in objects:
            for attr, child in inspect.getmembers(obj):
                if getattr(child, '__module__', None) != name:
                    continue
                if inspect.isfunction(child):
                    new_names.append(attr)
                elif inspect.isclass(child):
                    for childattr, grandchild in inspect.getmembers(child, inspect.isfunction):
                        if grandchild.__module__ != name:
                            continue
                        new_names.append('%s.%s' % (attr, childattr))
        new_names.sort(key=lambda s: s.lower())
        return new_names


def setup(app):
    app.setup_extension('sphinx.ext.autosummary')
    app.add_directive('autosummary', Autoautosummary)
    return {'version': '0.1', 'parallel_read_safe': True}

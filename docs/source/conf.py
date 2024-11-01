# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from datetime import date

project = 'Weasyl'
copyright = f'{date.today().year}, Weasyl'
author = 'Weasyl'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
   'sphinx.ext.duration',
   'sphinx.ext.doctest',
   'sphinx.ext.autodoc',
   'sphinx.ext.autosummary',
   'autodoc2',
   'myst_parser',
   'sphinx_copybutton',
]
autodoc2_packages = [
    {
        "path": "../../libweasyl",
    },
    {
        "path": "../../weasyl",
    },
]
autodoc2_render_plugin = "myst"
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# -- HTML output -------------------------------------------------

html_theme = "sphinx_book_theme"
html_logo = "_static/img/logo-mark-light.svg"
html_favicon = "_static/img/favicon.svg"
html_title = "Weasyl"
html_theme_options = {
    "home_page_in_toc": True,
    "show_toc_level": 2,
    "repository_url": "https://github.com/Weasyl/weasyl",
    "repository_branch": "main",
    "path_to_docs": "docs/source",
    "use_repository_button": True,
    "use_edit_page_button": True,
    "use_issues_button": True,
}
html_last_updated_fmt = ""
html_static_path = ['_static']



# -- Options for MyST -------------------------------------------------
# https://myst-parser.readthedocs.io/en/v0.15.1/syntax/optional.html#linkify
myst_heading_anchors = 2
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
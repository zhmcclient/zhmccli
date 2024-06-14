#
# Configuration file for Sphinx builds for the zhmccli project.
#
# Originally created by sphinx-quickstart, but then manually maintained.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys
import os
import io
import re


def get_version(version_file):
    """
    Execute the specified version file and return the value of the __version__
    global variable that is set in the version file.

    Note: Make sure the version file does not depend on any packages in the
    requirements list of this package (otherwise it cannot be executed in
    a fresh Python environment).
    """
    with open(version_file, encoding='utf-8') as fp:
        version_source = fp.read()
    _globals = {}
    exec(version_source, _globals)  # pylint: disable=exec-used
    return _globals['__version__']


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '1.3'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.extlinks',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',   # disabed, raises anexception
    'sphinx.ext.ifconfig',
    'sphinx_git',            # requires 'sphinx-git' Python package
    # Note: sphinx_rtd_theme is not compatible with sphinxcontrib.fulltoc,
    # but since it already provides a full TOC in the navigation pane, the
    # sphinxcontrib.fulltoc extension is not needed.
    'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The encoding of source files.
source_encoding = 'utf-8'

# The master toctree document.
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if on_rtd:
    master_doc = 'index'
else:
    master_doc = 'docs/index'

# General information about the project.
project = 'zhmccli'
copyright = 'IBM'
author = 'IBM Z KVM OpenStack Team'

# The short description of the package.
_short_description = 'A CLI for the IBM Z HMC'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

# The short X.Y version.
# Note: We use the full version in both cases (e.g. 'M.N.U' or 'M.N.U.dev0').
version = get_version(os.path.join('..', 'zhmccli', '_version.py'))

# The full version, including alpha/beta/rc tags.
release = version

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["tests", ".tox", ".git", "attic", "dist", "build",
                    "build_doc", "zhmccli.egg-info", ".eggs", "README.*"]

# The reST default role (used for this markup: `text`) to use for all
# documents. None means it is rendered in italic, without a link.
default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
#keep_warnings = False

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


# -- Options for Napoleon extension ---------------------------------------

# Enable support for Google style docstrings. Defaults to True.
napoleon_google_docstring = True

# Enable support for NumPy style docstrings. Defaults to True.
napoleon_numpy_docstring = False

# Include private members (like _membername). False to fall back to Sphinx’s
# default behavior. Defaults to False.
napoleon_include_private_with_doc = False

# Include special members (like __membername__). False to fall back to Sphinx’s
# default behavior. Defaults to True.
napoleon_include_special_with_doc = True

# Use the .. admonition:: directive for the Example and Examples sections,
# instead of the .. rubric:: directive. Defaults to False.
napoleon_use_admonition_for_examples = False

# Use the .. admonition:: directive for Notes sections, instead of the
# .. rubric:: directive. Defaults to False.
napoleon_use_admonition_for_notes = False

# Use the .. admonition:: directive for References sections, instead of the
# .. rubric:: directive. Defaults to False.
napoleon_use_admonition_for_references = False

# Use the :ivar: role for instance variables, instead of the .. attribute::
# directive. Defaults to False.
napoleon_use_ivar = True

# Use a :param: role for each function parameter, instead of a single
# :parameters: role for all the parameters. Defaults to True.
napoleon_use_param = True

# Use the :rtype: role for the return type, instead of inlining it with the
# description. Defaults to True.
napoleon_use_rtype = True


# -- Options for viewcode extension ---------------------------------------

# Follow alias objects that are imported from another module such as functions,
# classes and attributes. As side effects, this option ... ???
# If false, ... ???.
# The default is True.
viewcode_import = True


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.
# See http://www.sphinx-doc.org/en/stable/theming.html for built-in themes.
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.
# See http://www.sphinx-doc.org/en/stable/theming.html for the options
# available for built-in themes.
# For options of the 'sphinx_rtd_theme', see
# https://sphinx-rtd-theme.readthedocs.io/en/latest/configuring.html
html_theme_options = {
    'style_external_links': False,
    'collapse_navigation': False,
}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If not defined, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = 'ld'

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (relative to this directory) to use as a favicon of
# the docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
html_extra_path = ['_extra']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Language to be used for generating the HTML full-text search index.
# Sphinx supports the following languages:
#   'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja'
#   'nl', 'no', 'pt', 'ro', 'ru', 'sv', 'tr'
#html_search_language = 'en'

# A dictionary with options for the search language support, empty by default.
# Now only 'ja' uses this config value
#html_search_options = {'type': 'default'}

# The name of a javascript file (relative to the configuration directory) that
# implements a search results scorer. If empty, the default will be used.
#html_search_scorer = 'scorer.js'

# Output file base name for HTML help builder.
htmlhelp_basename = project+'_doc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
'papersize': 'a4paper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',

# Latex figure (float) alignment
#'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, project+'.tex', _short_description, author, 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, project, _short_description, [author], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, project, _short_description,
     author, project, _short_description,
     'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
#texinfo_no_detailmenu = False


# -- Options for autodoc extension ----------------------------------------
# For documentation, see
# http://www.sphinx-doc.org/en/stable/ext/autodoc.html

# Selects what content will be inserted into a class description.
# The possible values are:
#   "class" - Only the class’ docstring is inserted. This is the default.
#   "both"  - Both the class’ and the __init__ method’s docstring are
#             concatenated and inserted.
#   "init"  - Only the __init__ method’s docstring is inserted.
# In all cases, the __init__ method is still independently rendered as a
# special method, e.g. when the :special-members: option is set.
autoclass_content = "both"

# Selects if automatically documented members are sorted alphabetically
# (value 'alphabetical'), by member type (value 'groupwise') or by source
# order (value 'bysource'). The default is alphabetical.
autodoc_member_order = "bysource"

# This value is a list of autodoc directive flags that should be automatically
# applied to all autodoc directives. The supported flags are:
# 'members', 'undoc-members', 'private-members', 'special-members',
# 'inherited-members' and 'show-inheritance'.
# If you set one of these flags in this config value, you can use a negated
# form, 'no-flag', in an autodoc directive, to disable it once.
autodoc_default_flags = []

# Functions imported from C modules cannot be introspected, and therefore the
# signature for such functions cannot be automatically determined. However, it
# is an often-used convention to put the signature into the first line of the
# function’s docstring.
# If this boolean value is set to True (which is the default), autodoc will
# look at the first line of the docstring for functions and methods, and if it
# looks like a signature, use the line as the signature and remove it from the
# docstring content.
autodoc_docstring_signature = True

# This value contains a list of modules to be mocked up. This is useful when
# some external dependencies are not met at build time and break the building
# process.
autodoc_mock_imports = []


# -- Options for intersphinx extension ------------------------------------
# For documentation, see
# http://www.sphinx-doc.org/en/stable/ext/intersphinx.html

# Defines the prefixes for intersphinx links, and the targets they resolve to.
# Example RST source for 'py2' prefix:
#     :func:`py2:platform.dist`
#
# Note: The URLs apparently cannot be the same for two different IDs; otherwise
#       the links for one of them are not being created. A small difference
#       such as adding a trailing backslash is already sufficient to work
#       around the problem.
#
# Note: This mapping does not control how links to datatypes of function
#       parameters are generated.
# TODO: Find out how the targeted Python version for auto-generated links
#       to datatypes of function parameters can be controlled.
#
intersphinx_mapping = {
  'py': ('https://docs.python.org/2/', None), # agnostic to Python version
  'py2': ('https://docs.python.org/2', None), # specific to Python 2
  'py3': ('https://docs.python.org/3', None), # specific to Python 3
}

intersphinx_cache_limit = 5

# -- Options for extlinks extension ---------------------------------------
# For documentation, see
# http://www.sphinx-doc.org/en/stable/ext/extlinks.html
#
# Defines aliases for external links that can be used as role names.
#
# This config value must be a dictionary of external sites, mapping unique
# short alias names to a base URL and a prefix:
# * key: alias-name
# * value: tuple of (base-url, prefix)
#
# Example for the config value:
#
#   extlinks = {
#     'issue': ('https://github.com/sphinx-doc/sphinx/issues/%s', 'Issue ')
#   }
#
# The alias-name can be used as a role in links. In the example, alias name
# 'issue' is used in RST as follows:
#   :issue:`123`.
# This then translates into a link:
#   https://github.com/sphinx-doc/sphinx/issues/123
# where the %s in the base-url was replaced with the value between back quotes.
#
# The prefix plays a role only for the link caption:
# * If the prefix is None, the link caption is the full URL.
# * If the prefix is the empty string, the link caption is the partial URL
#   given in the role content ("123" in this case.)
# * If the prefix is a non-empty string, the link caption is the partial URL,
#   prepended by the prefix. In the above example, the link caption would be
#   "Issue 123".
#
# You can also use the usual "explicit title" syntax supported by other roles
# that generate links to set the caption. In this case, the prefix is not
# relevant.
# For example, this RST:
#   :issue:`this issue <123>`
# results in the link caption "this issue".

extlinks = {
}

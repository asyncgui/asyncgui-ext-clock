# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import importlib.metadata

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = 'asyncgui-ext-clock'
copyright = '2024, Mitō Nattōsai'
author = 'Mitō Nattōsai'
release = importlib.metadata.version(project)

rst_epilog = """
.. |ja| replace:: 🇯🇵
"""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    # 'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    # 'sphinx_tabs.tabs',

]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
language = 'en'
add_module_names = False
gettext_auto_build = False
gettext_location = False


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "furo"
html_static_path = ['_static']
# html_theme_options = {
#     "use_repository_button": True,
#     "repository_url": r"https://github.com/asyncgui/asyncpygame",
#     "use_download_button": False,
# }


# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration
todo_include_todos = True


# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'kivy': ('https://kivy.org/doc/master', None),
    'trio': ('https://trio.readthedocs.io/en/stable/', None),
    'asyncgui': ('https://asyncgui.github.io/asyncgui/', None),
    # 'pygame': ('https://pyga.me/docs/', None),
}


# -- Options for autodoc extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
# autodoc_mock_imports = ['pygame', ]
autodoc_default_options = {
#    'members': True,
#    'undoc-members': True,
   'no-show-inheritance': True,
}


# -- Options for tabs extension ---------------------------------------
# https://sphinx-tabs.readthedocs.io/en/latest/
sphinx_tabs_disable_tab_closing = True


def modify_signature(app, what: str, name: str, obj, options, signature, return_annotation: str,
                     prefix="asyncgui_ext.clock.",
                     len_prefix=len("asyncgui_ext.clock."),
                     group1={'ClockEvent', },
                     ):
    if not name.startswith(prefix):
        return (signature, return_annotation, )
    name = name[len_prefix:]
    if name in group1:
        print(f"Hide the signature of {name!r}")
        return ('', None)
    return (signature, return_annotation, )


def setup(app):
    app.connect('autodoc-process-signature', modify_signature)

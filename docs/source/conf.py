# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from __future__ import annotations

from datetime import datetime

from eagleclasslists import _info

project = "eagleclasslists"
copyright = f"{datetime.now().year}, Benjamin Davis"
author = _info.__author__
release = _info.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinxcontrib.autoprogram",
    "sphinx.ext.viewcode",
    "sphinx_prompt",
    "sphinx_collapse",
    "myst_parser",
]
autosummary_generate = True  # Turn on sphinx.ext.autosummary

myst_header_anchors = 2

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = []

html_theme_options = {
    "collapse_navigation": False,
}

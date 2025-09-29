# Reference: http://www.sphinx-doc.org/en/master/config
import os
import sys
sys.path.insert(0, os.path.abspath('../src/err-stackstorm'))
from errst2lib.version import ERR_STACKSTORM_VERSION

project = "err-stackstorm"
copyright = "2019-2022, err-stackstorm contributors"
author = "err-stackstorm contributors"
release = ERR_STACKSTORM_VERSION

master_doc = "index"
extensions = []
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

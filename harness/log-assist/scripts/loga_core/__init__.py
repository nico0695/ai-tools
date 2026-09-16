"""Shared library for the log-assist scripts.

Everything a script needs that is not specific to its own question lives here:
reading files, parsing Dex Player lines, the CLI contract, analysis-folder layout
and citations. A script never imports another script.

Python 3.11+, standard library only.
"""

__version__ = "0.1"

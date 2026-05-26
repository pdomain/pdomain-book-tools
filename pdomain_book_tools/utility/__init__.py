"""Utility helpers: timing decorators and Jupyter-widget helpers.

This package previously had no ``__init__.py`` at all (R-08); it now
exposes its two submodules as a stable surface so consumers can do
``from pdomain_book_tools.utility import timing``.
"""

from pdomain_book_tools.utility import ipynb_widgets, timing

__all__ = ["ipynb_widgets", "timing"]

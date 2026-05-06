"""pd-book-tools: tools for working with public domain book scans."""

# Version is generated at build time by hatch-vcs into _version.py.
# In an editable / source-tree checkout where _version.py hasn't been
# generated yet, fall back to importlib.metadata (works once installed).
try:
    from pd_book_tools._version import __version__, version  # noqa: F401
except ImportError:  # pragma: no cover - fallback for unbuilt source trees
    try:
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as _pkg_version

        try:
            __version__ = _pkg_version("pd-book-tools")
        except PackageNotFoundError:
            __version__ = "0.0.0+unknown"
    except ImportError:
        __version__ = "0.0.0+unknown"
    version = __version__

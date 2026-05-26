"""Layout-detector adapters.

Currently ships exactly one model adapter: :mod:`pp_doclayout`. Custom
adapters can be added under this directory and wired into
:func:`pdomain_book_tools.layout.registry.get_detector` (typically via a fork
or local patch — the registry is a closed switch by design).
"""

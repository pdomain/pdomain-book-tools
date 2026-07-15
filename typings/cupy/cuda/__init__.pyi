"""Stub for ``cupy.cuda`` — only the surface this repo uses.

``cupy.cuda.is_available()`` gates GPU-dependent test fixtures
(``tests/conftest.py``); ``Device.id`` backs ``cupy.ndarray.device`` in the
top-level ``cupy`` stub.
"""

class Device:
    @property
    def id(self) -> int: ...

def is_available() -> bool: ...

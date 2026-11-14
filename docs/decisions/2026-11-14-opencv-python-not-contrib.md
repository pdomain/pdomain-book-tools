---
Status: active
Owner: CT
Created: 2026-11-14
Last verified: 2026-11-14
Kind: decision
---

# Depend on opencv-python, not opencv-contrib-python

## Agent Index

- **Kind:** decision
- **Status:** active
- **Read when:** changing the OpenCV dependency, adding a `cv2` call from a
  contrib module, debugging `import cv2` failures, or installing on a server or
  container without a desktop.
- **Search terms:** opencv-python, opencv-contrib-python, headless, cv2 clash,
  mixed cv2 files, module 'cv2' has no attribute 'typing', libxcb.so.1,
  libGL, python-doctr opencv, exclude-dependencies, --excludes.

As of 2026-11-14, pdomain-book-tools depends on `opencv-python>=4.12.0.88` and
on no other OpenCV package. It used to depend on `opencv-contrib-python`.
python-doctr requires `opencv-python` by name. Declaring the same package
means every install holds exactly one copy of OpenCV.

The change fixes broken installs of pdomain-ocr-cli and pdomain-ocr-simple-gui.
It does not remove the need for X11 and OpenGL libraries on servers. That
remains a documented install requirement.

## Context

### The four OpenCV packages on PyPI

PyPI publishes the same OpenCV release in four builds. They differ on two
things: whether they include the extra "contrib" modules, and whether they can
open windows on screen. Sizes are for the 5.0.0.93 manylinux x86_64 wheels.

| Package | Contrib modules | Can open windows | Wheel size | Needs X11 and OpenGL libraries |
|---|---|---|---|---|
| `opencv-python` | no | yes | 71.1 MB | yes |
| `opencv-contrib-python` | yes | yes | 79.2 MB | yes |
| `opencv-python-headless` | no | no | 56.6 MB | no |
| `opencv-contrib-python-headless` | yes | no | 64.7 MB | no |

The contrib modules include `aruco`, `xfeatures2d`, `ximgproc`, `face`,
`text`, `tracking` and about a dozen more. A contrib build contains everything
in the matching plain build.

Window support exists for calls such as `cv2.imshow`. The builds that have it
link against libxcb, libGL and related desktop libraries at import time. They
fail on `import cv2` when those libraries are missing, even if the code never
opens a window.

### Why two OpenCV packages break an install

All four packages install into the same `cv2` folder in `site-packages`.
Neither pip nor uv knows they conflict. Each treats them as unrelated packages,
installs both, and lets the second overwrite some of the first one's files.
uv installs wheels in parallel, so which files win can change from one install
to the next.

Before this change, every CLI and GUI install held two OpenCV packages:

- pdomain-book-tools required `opencv-contrib-python>=5.0.0.93`.
- python-doctr 1.1.0, the version on PyPI, requires
  `opencv-python>=4.5.0,<6.0.0`.

On 2026-11-14 this broke a real install. A GPU install of pdomain-ocr-cli on
omarchy-main finished without error, then failed on the first page with
`module 'cv2' has no attribute 'typing'`. Comparing it with a clean install
showed mixed files, including `cv2/typing/__init__.py` and
`cv2/qt/plugins/libqxcb.so`. Other installs of the same versions worked,
because the parallel install happened to finish in a different order.

The development environment was mixed too, and in a worse way. Its lock file
held `opencv-python` 4.14.0.94, pulled in by the pinned python-doctr git
commit, next to `opencv-contrib-python` 5.0.0.93. The `cv2` folder held files
from two different OpenCV major versions.

### Why contrib was never needed

pdomain-book-tools uses only core OpenCV functions. These include
thresholding, blurring, morphology, contours, connected components, CLAHE,
`warpAffine` and `remap`, resizing, drawing text, and image reading, writing
and encoding. No library code calls a contrib module or opens a window.

The contrib requirement dates from an earlier rule in `tests/test_packaging.py`.
That rule kept contrib because it is a superset of the plain package. It
checked only this library's own `pyproject.toml`, so it could not see the
second OpenCV package that python-doctr adds.

### How the dependency reached contrib

The OpenCV dependency changed three times before this decision:

1. **2026-05-06, `ffb5e4b`.** `pyproject.toml` declared both `opencv-python`
   and `opencv-contrib-python`. The commit dropped `opencv-python` and kept
   contrib as the superset, citing H-17 in `docs/review/bugs-high.md`. That
   file was deleted in `288ea77`; read it with
   `git show 288ea77^:docs/review/bugs-high.md`. The commit added
   `tests/test_packaging.py`. Its message records an audit that found only
   core `cv2` calls even then.
2. **2026-06-06, `7ad7bc4`.** The library switched to
   `opencv-contrib-python-headless`. The full build ships Qt plugins under
   `cv2/qt/plugins` and sets `QT_QPA_PLATFORM_PLUGIN_PATH` when imported. That
   broke the PyQt6 desktop window of pdomain-ocr-simple-gui with
   `Could not load the Qt platform plugin 'xcb'`.
3. **2026-06-06, `1e416bc`.** The same day, that switch was reverted. The
   desktop window had been dropped, since simple-gui became browser-only.
   The commit also noted that the `[gpu]` extra then held `opencv-cuda`, which
   requires the full `opencv-python`, so headless gave GPU installs two OpenCV
   packages.

None of the three commits accounted for python-doctr. Its `opencv-python`
requirement meant that every contrib or headless declaration, from `ffb5e4b`
onward, gave every install two OpenCV packages, with or without `[gpu]`.
`opencv-cuda` was only an extra source of the same clash. It left the `[gpu]`
extra on 2026-11-10 in `b868a2a`.

## Decision

This library, pdomain-book-tools, declares `opencv-python>=4.12.0.88` in
`[project].dependencies` and no other OpenCV package. Library code uses only
modules that `opencv-python` ships. An application that uses this library may
still choose a different OpenCV build for itself, as described under
Consequences.

### Why the version floor returns to 4.12.0.88

The floor goes back to `>=4.12.0.88`, the value before commit `512b1ae`. That
commit raised every stale floor to the installed version, which made
`opencv-contrib-python>=5.0.0.93`. The 5.0 floor reflected no API need.

A 5.0 floor cannot be kept. The development environment pins python-doctr to
git commit `390330e` in `[tool.uv.sources]`. That commit builds as
python-doctr 1.0.2a0 and requires `opencv-python>=4.5.0,<5.0.0`. With a 5.0
floor, `uv lock` has no solution; its error on 2026-11-14 named that
requirement.

The two environments now resolve different OpenCV major versions:

| Environment | python-doctr | OpenCV |
|---|---|---|
| Development and CI (`uv.lock`) | git commit `390330e` | `opencv-python` 4.14.0.94 |
| User installs from published metadata | 1.1.0 from PyPI | `opencv-python` 5.0.0.93 |

`[tool.uv.sources]` applies only inside this repository, so published wheels
ask for plain `python-doctr`. Tests therefore run on OpenCV 4 while users run
OpenCV 5. The 2026-11-14 container install tests ran OpenCV 5.0.0.93, and
their OCR text contained every word of the reference page. Moving the
development pin to python-doctr 1.1.0 would close this gap and is a separate
change.

### How the rule is enforced

Three tests in `tests/test_packaging.py` enforce the rule:

- `test_declares_only_opencv_python`: `pyproject.toml` declares
  `opencv-python` and no other OpenCV package.
- `test_environment_has_one_opencv_distribution`: the resolved environment
  holds exactly one OpenCV package, `opencv-python`. This catches a dependency
  upgrade that brings a second `cv2` provider back.
- `test_source_uses_no_contrib_only_module`: library code calls no
  contrib-only `cv2` module.

## Alternatives considered

**Keep `opencv-contrib-python`.** Rejected. Package metadata cannot stop
python-doctr from adding `opencv-python`, so every install would keep two
packages.

**Switch to a headless package.** Rejected for the library. Headless builds
need no desktop libraries, but python-doctr would still add `opencv-python`
beside it, giving two packages again.

**Have the installers swap in a headless build.** Not adopted now. An installer
can run `uv tool install --excludes <file> --with <headless package>`, where
the file lists the packages to drop. The test on 2026-11-14 excluded
`opencv-python` and `opencv-contrib-python` and added
`opencv-contrib-python-headless`. The OCR text file it produced was identical
to the one from a working desktop-build install. This swap also removes the
need for desktop libraries. It only helps installs that go through the
installer scripts, though. Manual installs and development environments would
not get it. It can still be added on top of this change later, to make server
installs simpler.

## Consequences

### What servers and containers still need

`opencv-python` can open windows, so `import cv2` needs X11 and OpenGL
libraries. Desktop Linux already has them. Minimal servers and container images
do not, and OCR fails with an error that `libxcb.so.1` cannot be found.

Install tests on 2026-11-14 covered Ubuntu 24.04.5, Ubuntu 22.04.5, Debian 13,
Fedora 45, AlmaLinux 9.8, Arch and openSUSE Tumbleweed. Every bare image failed
this way. Every one worked after adding these packages:

| Distribution family | Packages |
|---|---|
| Debian and Ubuntu | `libgl1 libsm6 libice6 libx11-6 libxext6 libxcb1`, plus `libglib2.0-0t64`, or `libglib2.0-0` on releases before Ubuntu 24.04 and Debian 13 |
| Fedora and AlmaLinux | `mesa-libGL libSM libICE libX11 libXext libxcb glib2` |
| Arch | `libglvnd mesa libsm libice libx11 libxext libxcb glib2` |
| openSUSE | `Mesa-libGL1 libSM6 libICE6 libX11-6 libXext6 libxcb1 libglib-2_0-0 libgthread-2_0-0` |

Alpine 3.24 is not supported for a different reason: PyTorch publishes no
musllinux wheels.

### Qt applications that import cv2

`opencv-python` is a full build, so it still ships the Qt plugins that caused
the 2026-06-06 desktop-window failure. No current pdomain application has a
Qt window. A future one that imports this library would hit the same plugin
clash. That application would need its own headless swap. It would follow the
steps in "If a contrib module is ever needed" below, with a headless package as
the chosen build. It would also use the installer flags from "Have the
installers swap in a headless build" under Alternatives considered. The
exception applies to that application only. This library keeps declaring
`opencv-python`.

### If a contrib module is ever needed

First, look for a replacement that avoids contrib. Many contrib functions have
an equivalent in scikit-image or take a few lines of NumPy.

If contrib is truly needed, keep this library's declared dependency as
`opencv-python`. Check for the module at run time, for example with
`hasattr(cv2, "ximgproc")`. If it is missing, raise an error that names the
package to install. Then let each application choose one OpenCV package and
drop the rest:

1. In the application's own development environment, list the unwanted
   packages under `exclude-dependencies` in `[tool.uv]`. Then add the chosen
   package, for example `opencv-contrib-python-headless`, as a direct
   dependency.
2. In the application's installers, pass
   `uv tool install --excludes <file> --with <chosen package>`. `uv tool install`
   ignores an installed package's own `[tool.uv]` settings, so the installer
   must pass these flags itself.
3. Keep a test like `test_environment_has_one_opencv_distribution` in the
   application, so a second OpenCV package
   fails CI instead of failing on a user's machine.

### What pdomain-ocr-cli and pdomain-ocr-simple-gui must do next

This change ships in pdomain-book-tools 0.31.3. pdomain-ocr-cli and
pdomain-ocr-simple-gui each pin pdomain-book-tools exactly at 0.31.0, so each
needs its pin raised to 0.31.3 and a new release.

The READMEs of pdomain-ocr-cli and pdomain-ocr-simple-gui list the server
packages above, so people installing on a server can find them.

## Supersedes / Superseded-by

- Supersedes: the rule that pdomain-book-tools depends on
  `opencv-contrib-python` because it is a superset of `opencv-python`. That
  rule had no decision record. It lived in commit `ffb5e4b`, the revert in
  `1e416bc`, and the old `tests/test_packaging.py`.
- Superseded by: none.

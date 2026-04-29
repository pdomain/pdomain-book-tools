"""Tests for image_processing.external_tools module."""

import pathlib
import subprocess
from unittest.mock import patch

import pytest

from pd_book_tools.image_processing.external_tools import run_gegl_c2g, run_optipng


class TestRunOptipng:
    @patch("pd_book_tools.image_processing.external_tools.subprocess.run")
    def test_invokes_optipng_with_expected_args(self, mock_run, tmp_path):
        """run_optipng should invoke 'optipng -o7 <abs path>'."""
        src = tmp_path / "image.png"
        src.touch()

        run_optipng(src)

        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        args = kwargs["args"]
        assert args[0] == "optipng"
        assert args[1] == "-o7"
        assert args[2] == src.absolute().as_posix()
        assert kwargs["shell"] is False
        assert kwargs["check"] is True

    @patch("pd_book_tools.image_processing.external_tools.subprocess.run")
    def test_propagates_subprocess_failure(self, mock_run, tmp_path):
        """A non-zero exit must surface as CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="optipng"
        )
        src = tmp_path / "missing.png"

        with pytest.raises(subprocess.CalledProcessError):
            run_optipng(src)


class TestRunGeglC2g:
    @patch("pd_book_tools.image_processing.external_tools.subprocess.run")
    def test_invokes_gegl_c2g_with_expected_args(self, mock_run, tmp_path):
        """run_gegl_c2g should invoke gegl with -- c2g and the optional options string."""
        source = tmp_path / "in.png"
        target = tmp_path / "out.png"
        source.touch()

        run_gegl_c2g(source, target, c2gOptions="radius=5")

        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        args = kwargs["args"]
        assert args[0] == "gegl"
        assert args[1] == source.absolute().as_posix()
        assert args[2] == "-o"
        assert args[3] == target.absolute().as_posix()
        assert args[4] == "--"
        assert args[5] == "c2g"
        assert args[6] == "radius=5"
        assert kwargs["shell"] is False
        assert kwargs["check"] is True

    @patch("pd_book_tools.image_processing.external_tools.subprocess.run")
    def test_default_options_empty_string(self, mock_run, tmp_path):
        source = pathlib.Path(tmp_path / "a.png")
        target = pathlib.Path(tmp_path / "b.png")
        run_gegl_c2g(source, target)
        args = mock_run.call_args.kwargs["args"]
        # last arg is the c2gOptions, default ""
        assert args[-1] == ""

"""Tests for image_processing.external_tools module."""

import pathlib
import subprocess
from unittest.mock import patch

import pytest

from pdomain_book_tools.image_processing.external_tools import run_gegl_c2g, run_optipng


class TestRunOptipng:
    @patch("pdomain_book_tools.image_processing.external_tools.subprocess.run")
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

    @patch("pdomain_book_tools.image_processing.external_tools.subprocess.run")
    def test_propagates_subprocess_failure(self, mock_run, tmp_path):
        """A non-zero exit must surface as CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="optipng"
        )
        src = tmp_path / "missing.png"

        with pytest.raises(subprocess.CalledProcessError):
            run_optipng(src)


class TestRunGeglC2g:
    @patch("pdomain_book_tools.image_processing.external_tools.subprocess.run")
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

    @patch("pdomain_book_tools.image_processing.external_tools.subprocess.run")
    def test_default_options_empty_string(self, mock_run, tmp_path):
        source = pathlib.Path(tmp_path / "a.png")
        target = pathlib.Path(tmp_path / "b.png")
        run_gegl_c2g(source, target)
        args = mock_run.call_args.kwargs["args"]
        # Empty c2gOptions must NOT add an empty-string arg (GEGL would reject it).
        # The argv ends after the "c2g" token.
        assert args[-1] == "c2g"
        assert "" not in args

    @patch("pdomain_book_tools.image_processing.external_tools.subprocess.run")
    def test_multi_flag_options_are_shlex_split(self, mock_run, tmp_path):
        """M-06: multi-token c2gOptions must be split into separate argv entries."""
        source = tmp_path / "in.png"
        target = tmp_path / "out.png"
        source.touch()

        run_gegl_c2g(source, target, c2gOptions="--samples 4 --iterations 10")

        args = mock_run.call_args.kwargs["args"]
        # The c2g token must be followed by the split flag tokens, not a single
        # concatenated string.
        c2g_idx = args.index("c2g")
        tail = args[c2g_idx + 1 :]
        assert tail == ["--samples", "4", "--iterations", "10"]
        assert "--samples 4 --iterations 10" not in args

    @patch("pdomain_book_tools.image_processing.external_tools.subprocess.run")
    def test_quoted_options_preserve_spaces(self, mock_run, tmp_path):
        """shlex.split must respect quoted multi-word values."""
        source = tmp_path / "in.png"
        target = tmp_path / "out.png"
        source.touch()

        run_gegl_c2g(source, target, c2gOptions='--label "two words" --n 3')

        args = mock_run.call_args.kwargs["args"]
        c2g_idx = args.index("c2g")
        tail = args[c2g_idx + 1 :]
        assert tail == ["--label", "two words", "--n", "3"]

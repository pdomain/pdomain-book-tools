import pathlib
import subprocess


def run_optipng(
    src: pathlib.Path,
):
    subprocess.run(
        args=[
            "optipng",
            "-o7",
            src.absolute().as_posix(),
        ],
        shell=False,
        check=True,
    )


def run_gegl_c2g(
    source_image_file: pathlib.Path,
    target_image_file: pathlib.Path,
    c2gOptions: str = "",
):
    subprocess.run(
        args=[
            "gegl",
            source_image_file.absolute().as_posix(),
            "-o",
            target_image_file.absolute().as_posix(),
            "--",
            "c2g",
            c2gOptions,
        ],
        shell=False,
        check=True,
    )

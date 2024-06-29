import os
import struct
from pathlib import Path
from os import PathLike

from .models import MPKFileInfo


def unpack_mpk(file: PathLike | str, extract_folder: PathLike | None = None):
    """
    unpack mpk file

    :param file: mpk file path
    :param extract_folder: extract folder path
    :return: None
    """
    mpk_path = Path(file)

    # create a folder
    if extract_folder:
        extract_folder = Path(extract_folder)
    else:
        extract_folder = mpk_path.with_name("extracted_" + mpk_path.stem)
    if not extract_folder.exists():
        os.makedirs(extract_folder)

    if not mpk_path.exists():
        raise FileNotFoundError(f"cannot find {file}")

    with mpk_path.open("rb") as mpk_file:
        # check if the file is a mpk file
        data = struct.unpack("4c", mpk_file.read(4))
        if data != (b"M", b"P", b"K", b"\x00"):
            raise ValueError("unknown file type!")

        _, file_count = struct.unpack("<2I", mpk_file.read(8))
        mpk_file.read(0x34)

        # index table
        files: list[MPKFileInfo] = []

        # read file table
        for i in range(file_count):
            files.append(MPKFileInfo.unpack(mpk_file.read(0x100)))

        for file_info in files:
            target_folder = extract_folder / Path(file_info.name).parent

            # create subdirectory
            if not target_folder.exists():
                target_folder.mkdir(parents=True)

            mpk_file.seek(file_info.offset)

            target_file = target_folder / Path(file_info.name).name
            with target_file.open("wb") as out:
                out.write(mpk_file.read(file_info.size))

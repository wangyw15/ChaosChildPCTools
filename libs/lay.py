import struct
import zlib
from os import PathLike
from pathlib import Path

from PIL import Image


def extract_lay_image(
        file: PathLike | str,
        extract_folder: PathLike | str | None = None,
        save_parts=True,
        save_composed=True
):
    """
    decrypt lay image file

    :param file: png/lay file path
    :param extract_folder: folder to extract the images
    :param save_parts: save the parts
    :param save_composed: save the composed image

    :return: None
    """
    file_path = Path(file)

    # get file paths
    if file_path.suffix == ".png":
        png_path = file_path
        lay_path = file_path.parent / (file_path.stem + "_.lay")
    elif file_path.stem.endswith("_") and file_path.suffix == ".lay":
        png_path = file_path.parent / (file_path.stem[:-1] + ".png")
        lay_path = file_path
    else:
        raise ValueError("file name error")

    # check if the files exist
    if not png_path.exists():
        raise FileNotFoundError(f"cannot find {png_path}")
    if not lay_path.exists():
        raise FileNotFoundError(f"cannot find {lay_path}")

    # read lay file
    with lay_path.open("rb") as lay_file:
        lay_raw_data = lay_file.read()

    # read lay data
    lay_data_compressed = lay_raw_data[:2] == b"\x78\x9c"
    lay_data = zlib.decompress(lay_raw_data) if lay_data_compressed else lay_raw_data

    lay_data_pointer = 0

    # the head of the file is the number of images and part blocks
    image_count, part_count = struct.unpack("<2I", lay_data[lay_data_pointer : lay_data_pointer + 8])
    lay_data_pointer += 8

    # image information following
    part_number: list[int] = []
    part_tree: list = []
    for i in range(image_count):
        part_tree.append(struct.unpack("<4b", lay_data[lay_data_pointer : lay_data_pointer + 4]))
        lay_data_pointer += 4

        part_number.append(
            struct.unpack("<I", lay_data[lay_data_pointer : lay_data_pointer + 4])[0]
        )  # the block number of image
        lay_data_pointer += 4

        lay_data_pointer += 4  # ?
    part_number.append(part_count)

    # get extract path
    if extract_folder:
        extract_folder = Path(extract_folder)
    else:
        extract_folder = file_path.parent / ("extracted_" + png_path.stem)
    parts_folder = extract_folder / "parts"
    composed_folder = extract_folder / "composed"

    # create extract folder
    extract_folder.mkdir(parents=True, exist_ok=True)
    if save_parts:
        parts_folder.mkdir(exist_ok=True)
    if save_composed:
        composed_folder.mkdir(exist_ok=True)

    # origin png file
    source_image = Image.open(png_path)

    # init the canvas
    canvas = Image.new("RGBA", (4000, 2000))

    # get the range of drawing block
    min_x, min_y, max_x, max_y = 0, 0, 0, 0

    # get the parts
    part_images = []
    part_position = []
    part_index = 0

    # TODO refact code
    for i in range(part_count + 1):
        # read part position in source image
        f1, f2, f3, f4 = 0, 0, 0, 0
        if lay_data_pointer < len(lay_data):
            f1, f2, f3, f4 = struct.unpack("<4f", lay_data[lay_data_pointer : lay_data_pointer + 16])
        lay_data_pointer += 16

        # image center
        f1 += 2000.0
        f2 += 1000.0

        if i == part_number[part_index]:
            if i != 0:
                part = canvas.crop((min_x, min_y, max_x + 30, max_y + 30))
                part_images.append(part)
                part_position.append((min_x, min_y, max_x + 30, max_y + 30))
                if save_parts:
                    part.save(parts_folder / (str(part_index) + ".png"))
                canvas = Image.new("RGBA", (4000, 2000))  # reset the Canvas
            part_index += 1
            min_x, min_y, max_x, max_y = int(f1), int(f2), int(f1), int(f2)
        part_block = source_image.crop((int(f3) - 1, int(f4) - 1, int(f3) + 29, int(f4) + 29))
        x, y = int(f1), int(f2)
        canvas.paste(part_block, (x, y))

        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    if save_composed:
        # only one image
        if image_count == 1:
            part_images[0].save(composed_folder / png_path.name)
            return

        part_index = 0
        path = [-1] * 7
        last = -1
        for i in range(image_count + 1):
            if i >= image_count or int(part_tree[i][3] / 0x10) <= last:  # last image is a leaf
                canvas = Image.new("RGBA", (4000, 2000))
                min_x, min_y, max_x, max_y = part_position[0]
                for k in range(last + 1):
                    if path[k] != -1:
                        x, y, z, w = part_position[path[k]]
                        min_x, max_x = min(min_x, x), max(max_x, x)
                        min_y, max_y = min(min_y, y), max(max_y, y)
                        canvas.paste(part_images[path[k]], (x, y), mask=part_images[path[k]])
                part = canvas.crop((min_x, min_y, max_x, max_y))
                part.save(composed_folder / (file_path.stem + str(part_index) + ".png"))
                part_index += 1
            if i < image_count:
                last = int(part_tree[i][3] / 0x10)
                path[last] = i

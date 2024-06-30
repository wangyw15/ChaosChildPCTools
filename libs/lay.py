import struct
import zlib
from os import PathLike
from pathlib import Path

from PIL import Image

CANVAS_SIZE = (4000, 4000)
SOURCE_TILE_SIZE = 32
DRAW_TILE_SIZE = SOURCE_TILE_SIZE


def extract_lay_image(
    file: PathLike | str,
    extract_folder: PathLike | str | None = None,
    save_parts=True,
    save_composed=True,
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

    # the head of the file is the number of parts and tiles
    part_count, tile_count = struct.unpack(
        "<2I", lay_data[lay_data_pointer : lay_data_pointer + 8]
    )
    lay_data_pointer += 8

    # image information following
    part_number: list[int] = []
    compose_tree: list = []
    for i in range(part_count):
        compose_tree.append(
            struct.unpack("<4b", lay_data[lay_data_pointer : lay_data_pointer + 4])
        )
        lay_data_pointer += 4

        part_number.append(
            struct.unpack("<I", lay_data[lay_data_pointer : lay_data_pointer + 4])[0]
        )  # the block number of image
        lay_data_pointer += 4

        # I have no idea about this segment
        lay_data_pointer += 4

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

    # source png file
    source_image = Image.open(png_path)

    # get the parts
    part_images = []
    part_position = []

    # draw parts
    for i_part in range(part_count):
        # calculate part tile count
        if i_part + 1 < part_count:
            part_tile_count = part_number[i_part + 1] - part_number[i_part]
        else:
            part_tile_count = tile_count - part_number[i_part]

        # compose tiles into parts
        canvas = Image.new("RGBA", CANVAS_SIZE)
        min_x, min_y, max_x, max_y = canvas.size[0], canvas.size[1], 0, 0

        for i_tile in range(part_tile_count):
            part_x, part_y, source_x, source_y = struct.unpack(
                "<4f", lay_data[lay_data_pointer : lay_data_pointer + 16]
            )
            lay_data_pointer += 16

            # part position relative to image center
            part_x += canvas.size[0] / 2
            part_y += canvas.size[1] / 2

            # copy from source image
            tile_image = source_image.crop(
                (
                    int(source_x) - 1,
                    int(source_y) - 1,
                    int(source_x) + SOURCE_TILE_SIZE - 1,
                    int(source_y) + SOURCE_TILE_SIZE - 1,
                )
            )

            # paste to canvas
            part_x, part_y = int(part_x), int(part_y)
            canvas.paste(tile_image, (part_x, part_y))

            # update drawing box
            min_x = min(min_x, part_x)
            min_y = min(min_y, part_y)
            max_x = max(max_x, part_x)
            max_y = max(max_y, part_y)

        # crop the part and append to list
        part_box = (min_x, min_y, max_x + DRAW_TILE_SIZE, max_y + DRAW_TILE_SIZE)
        cropped_part = canvas.crop(part_box)
        part_position.append(part_box)
        part_images.append(cropped_part)

        if save_parts:
            cropped_part.save(parts_folder / (str(i_part) + ".png"))

    if save_composed:
        # only one part
        if part_count == 1:
            part_images[0].save(composed_folder / png_path.name)
            return

        # compose image by path
        compose_path = [-1] * 7
        last = -1

        i_image = 0
        for i_part in range(part_count + 1):
            # path meets end
            if i_part >= part_count or int(compose_tree[i_part][3] / 0x10) <= last:
                canvas = Image.new("RGBA", CANVAS_SIZE)
                # crop image
                min_x, min_y, max_x, max_y = canvas.size[0], canvas.size[1], 0, 0

                # composing
                for i_path in range(last + 1):
                    if compose_path[i_path] != -1:
                        x, y, a, b = part_position[compose_path[i_path]]
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, a)
                        max_y = max(max_y, b)
                        canvas.paste(
                            part_images[compose_path[i_path]],
                            (x, y),
                            part_images[compose_path[i_path]],
                        )
                cropped_image = canvas.crop((min_x, min_y, max_x, max_y))
                cropped_image.save(composed_folder / (str(i_image) + ".png"))
                i_image += 1

            # iter tree by DFS
            if i_part < part_count:
                last = int(compose_tree[i_part][3] / 0x10)
                compose_path[last] = i_part

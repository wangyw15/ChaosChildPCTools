import libs
from pathlib import Path
from argparse import ArgumentParser

main_parser = ArgumentParser(description="MAGES Engine helper")
subparsers = main_parser.add_subparsers(title="Sub commands", description="Available sub commands", dest="subcommand")

view_mpk_parser = subparsers.add_parser("view-mpk", help="View mpk file")
view_mpk_parser.add_argument("input", help="Path to the mpk file", type=str)

unpack_mpk_parser = subparsers.add_parser("unpack-mpk", help="Unpack mpk file")
unpack_mpk_parser.add_argument("input", help="Path to the mpk file", type=str)
unpack_mpk_parser.add_argument("output", help="Path to the unpacked folder", type=str, nargs="?")

extract_lay_parser = subparsers.add_parser("extract-lay", help="Extract lay image")
extract_lay_parser.add_argument("input", help="Path to the lay file", type=str)
extract_lay_parser.add_argument("output", help="Path to the extract images folder", type=str, nargs="?")

extract_gxt_parser = subparsers.add_parser("extract-gxt", help="Extract gxt image")
extract_gxt_parser.add_argument("input", help="Path to the gxt file", type=str)
extract_gxt_parser.add_argument("output", help="Path to the extract image path/folder", type=str, nargs="?")


def main():
    args = main_parser.parse_args()

    input_files = []
    input_path = Path(args.input)

    if not args.output:
        output_path = Path(input_path.parent) / "cctools"
    else:
        output_path = Path(args.output)

    if input_path.is_file():
        input_files.append(input_path)
    elif input_path.is_dir():
        input_files = list(input_path.glob("*"))

    if not args.subcommand:
        main_parser.print_help()
    elif args.subcommand == "view-mpk":
        # print in csv format
        print("MPK, Index, Name, Size")
        for f in input_files:
            if f.suffix.lower() == ".mpk":
                files = libs.get_files_info_in_mpk(f)
                for i in files:
                    print("{}, {}, {}, {}".format(f, i.index, i.name, i.size))
    elif args.subcommand == "unpack-mpk":
        for f in input_files:
            if f.suffix.lower() == ".mpk":
                if len(input_files) == 1:
                    libs.unpack_mpk(f, output_path.parent / f.stem)
                else:
                    libs.unpack_mpk(f, output_path / f.stem)
    elif args.subcommand == "extract-lay":
        for f in input_files:
            if f.suffix.lower() == ".lay":
                if len(input_files) == 1:
                    libs.extract_lay_image(f, output_path.parent / f.stem)
                else:
                    libs.extract_lay_image(f, output_path / f.stem)
    elif args.subcommand == "extract-gxt":
        for f in input_files:
            if f.suffix.lower() == ".gxt":
                if len(input_files) == 1:
                    libs.extract_gxt_image(f, output_path.parent / f.stem)
                else:
                    libs.extract_gxt_image(f, output_path / (f.stem + ".png"))


if __name__ == "__main__":
    main()

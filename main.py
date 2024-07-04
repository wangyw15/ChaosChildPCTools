import libs
from argparse import ArgumentParser

main_parser = ArgumentParser(description="MAGES Engine helper")
subparsers = main_parser.add_subparsers(title="Sub commands", description="Available sub commands", dest="subcommand")

view_mpk_parser = subparsers.add_parser("view-mpk", help="View mpk file")
view_mpk_parser.add_argument("input", help="Path to the mpk file", type=str)

unpack_mpk_parser = subparsers.add_parser("unpack-mpk", help="Unpack mpk file")
unpack_mpk_parser.add_argument("input", help="Path to the mpk file", type=str)
unpack_mpk_parser.add_argument("output", help="Path to the unpacked dir", type=str)

extract_lay_parser = subparsers.add_parser("extract-lay", help="Extract lay image")
extract_lay_parser.add_argument("input", help="Path to the lay file", type=str)
extract_lay_parser.add_argument("output", help="Path to the extract images", type=str)

extract_gxt_parser = subparsers.add_parser("extract-gxt", help="Extract gxt image")
extract_gxt_parser.add_argument("input", help="Path to the gxt file", type=str)
extract_gxt_parser.add_argument("output", help="Path to the extract images", type=str)


def main():
    args = main_parser.parse_args()

    if not args.subcommand:
        main_parser.print_help()
    elif args.subcommand == "view-mpk":
        files = libs.get_files_info_in_mpk(args.input)
        for i in files:
            print(i.name)
    elif args.subcommand == "unpack-mpk":
        libs.unpack_mpk(args.input, args.output)
    elif args.subcommand == "extract-lay":
        libs.extract_lay_image(args.input, args.output)
    elif args.subcommand == "extract-gxt":
        libs.extract_gxt_image(args.input, args.output)


if __name__ == "__main__":
    main()

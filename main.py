from eos_flattener.read_info import ReadInfo
from eos_flattener.write_info import WriteInfo
from eos_flattener.store import Store
from eos_flattener.file_analyser.kaomado import FileAnalyserKaomado
from eos_flattener.file_analyser.script import FileAnalyserScript
from eos_flattener.file_analyser.actor_list import FileAnalyzerActorListBin
from eos_flattener.file_analyser.monster_xml import FileAnalyzerMonsterXML
from eos_flattener.file_analyser.bin_files import FileAnalyserBinPack
from eos_flattener.file_analyser.object_list_bin import FileAnalyserObjectBin
from eos_flattener.file_analyser.data_cd import FileAnalyserDataCD
from eos_flattener.file_analyser.str import FileAnalyserStr
from eos_flattener.file_analyser.bg_list import FileAnalyserBgList
from eos_flattener.file_analyser.waza_p import FileAnalyserWazaP
from eos_flattener.file_analyser.sprite_data import FileAnalyserSpriteData
from eos_flattener.file_analyser.level_list import FileAnalyserLevelList
import argparse
import os

parser = argparse.ArgumentParser(description = "Transform an EoS rom in a format suitable for Git tracking")

parser.add_argument("cache", type=str, help="Path where data will be cached between runs")

subparsers = parser.add_subparsers(dest="subcommand")

parse_extract = subparsers.add_parser("unpack", help="Extract files of a .nds files")
parse_extract.add_argument("source", type=str)
parse_extract.add_argument("dest", type=str)

parse_repack = subparsers.add_parser("repack", help="Repack extracted files into a .nds")
parse_repack.add_argument("source", type=str)
parse_repack.add_argument("dest", type=str)

args = parser.parse_args()

os.makedirs(args.cache, exist_ok=True)
store = Store(os.path.join(args.cache, "store"))

#TODO: auto-determine region. Ugly hack for now.

ANALYZERS = [
    FileAnalyserKaomado(),
    FileAnalyserScript("EoS_NA"),
    FileAnalyzerActorListBin(),
    FileAnalyzerMonsterXML("EoS_NA"),
    FileAnalyserBinPack(),
    FileAnalyserObjectBin(),
    #FileAnalyserDataCD(),
    FileAnalyserStr("EoS_NA"),
    FileAnalyserBgList(),
    FileAnalyserWazaP(),
    FileAnalyserSpriteData(),
    FileAnalyserLevelList()
]

if args.subcommand == "unpack":
    print("extracting file (slow)")
    a = ReadInfo(args.source, store, os.path.join(args.cache, "extract_temp"))
    print("extracted")

    a.run_analyzers(ANALYZERS)

    print("writing result")
    a.dump_data(args.dest)
    print("written")
elif args.subcommand == "repack":
    print("loading files (slow)")
    a = WriteInfo(args.source, store)
    print("done")

    a.run_analyzers(ANALYZERS)

    print("writing rom")
    a.write_rom(args.dest, os.path.join(args.cache, "repack_temp"))
    print("writing rom done")
else:
    raise
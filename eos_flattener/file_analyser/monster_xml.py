from .file_analyser_base import FileAnalyserBase
import json
from skytemple_rust.st_md import Md
from skytemple_rust.st_md import MdWriter
from eos_flattener.executer import Executer
from skytemple_files.data.monster_xml import monster_xml_export
from skytemple_files.data.monster_xml import monster_xml_import
from skytemple_files.data.monster_xml import GenderedConvertEntry
from skytemple_files.common.xml_util import prettify
from xml.etree import ElementTree
import os

class FileAnalyzerMonsterXML(FileAnalyserBase):
    def __init__(self, game_version):
        self.game_version = game_version
        super().__init__()

    def on_read(self, store, read_info):
        class ExportAllMonsterXML(Executer):
            UNIQUE_NAME = "all-monster-xml-dec-2"

            def execute(self, store, hash):
                print("decoding monster XML")

                monster_md_f = open(store.get_derivation_path(self.input["monster_md_hash"]), "rb")
                monster_md_b = monster_md_f.read()
                monster_md_f.close()

                md = Md(monster_md_b)

                map_to_hash = {}

                for monster_id in range(600):
                    print("decoding monster pair " + str(monster_id))
                    have_second = monster_id < 555
                    md_0 = md.get_by_index(monster_id)
                    md_1 = None
                    if have_second:
                        md_1 = md.get_by_index(monster_id + 600)
                    export = monster_xml_export(
                        self.input["game_version"],
                        md_0,
                        md_1,
                        None, None, None, None,
                        None, None,
                        None, None,
                        None, None
                    )

                    map_to_hash[str(monster_id)] = store.add_byte(prettify(export).encode("utf-8"))

                with open(store.get_derivation_path(hash), "w") as f:
                    json.dump(map_to_hash, f)
        
        json_data_hash = store.get_or_execute(ExportAllMonsterXML({
            "monster_md_hash": read_info.get_hash_and_remove("rom/BALANCE/monster.md"),
            "game_version": self.game_version
        }))

        map_to_hash = None
        with open(store.get_derivation_path(json_data_hash), "r") as f:
            map_to_hash = json.load(f)
        
        for id in map_to_hash:
            read_info.set_hash_for_file("monster/" + id + "/data.xml", map_to_hash[id])
            
    
    def on_write(self, store, write_info):
        class ImportAllMonsterXML(Executer):
            UNIQUE_NAME = "all-monster-xml-enc-3"

            def execute(self, store, hash):
                print("encoding monster xml")

                mock_md_bytes = bytes([0, 0, 0, 0, 1155 % 256, int(1155 / 256), 0, 0] + [0] * 68 * 1155)
                md = Md(mock_md_bytes)

                for monster_base_id in range(600):
                    monster_xml_file_hash = self.input["monster_xml_files"][monster_base_id]
                    xml = ElementTree.parse(store.get_derivation_path(monster_xml_file_hash)).getroot()

                    have_second = monster_base_id < 555
                    md_0 = md.get_by_index(monster_base_id)
                    mon_0 = GenderedConvertEntry(md_0, None, None)
                    
                    md_1 = None
                    mon_1 = None
                    if have_second:
                        md_1 = md.get_by_index(monster_base_id + 600)
                        mon_1 = GenderedConvertEntry(md_1, None, None)

                    monster_xml_import(
                        xml,
                        mon_0,
                        mon_1,
                        None, None, None, None, None, None
                    )

                    md[monster_base_id] = mon_0.md_entry
                    if have_second:
                        md[monster_base_id + 600] = mon_1.md_entry
                
                md_bytes = MdWriter().write(md)
                out = {
                    "md_bytes_hash": store.add_byte(md_bytes)
                }

                with open(store.get_derivation_path(hash), "w") as f:
                    json.dump(out, f)


        monster_id_to_xml_file_hash = {}
        for monster_id in range(600):
            monster_file_hash = write_info.get_hash_and_remove("monster/" + str(monster_id) + "/data.xml")
            monster_id_to_xml_file_hash[monster_id] = monster_file_hash
        

        link_to_files_json_hash = store.get_or_execute(ImportAllMonsterXML({
            "monster_xml_files": monster_id_to_xml_file_hash
        }))

        out = None
        with open(store.get_derivation_path(link_to_files_json_hash)) as f:
            out = json.load(f)

        write_info.set_hash_for_file("rom/BALANCE/monster.md", out["md_bytes_hash"])


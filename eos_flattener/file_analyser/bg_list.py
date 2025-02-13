from skytemple_files.graphics.bg_list_dat.handler import BgListDatHandler
from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer
import json
from skytemple_files.graphics.bg_list_dat._model import BgListEntry

class FileAnalyserBgList(FileAnalyserBase):

    def on_read(self, store, read_info):
        class ExtractBgList(Executer):
            UNIQUE_NAME = "bglist-to-json-2"

            def execute(self, store, hash):
                print("Extracting bg_list")

                bg_list_bytes = None
                with open(store.get_derivation_path(self.input["bg_list_hash"]), "rb") as f:
                    bg_list_bytes = f.read()
                
                bg_list = BgListDatHandler.deserialize(bg_list_bytes)

                to_encode = []

                for level in bg_list.level:
                    to_encode.append({
                        "bpl": level.bpl_name,
                        "bpc": level.bpc_name,
                        "bma": level.bma_name,
                        "bpas": level.bpa_names
                    })

                with open(store.get_derivation_path(hash), "w") as f:
                    json.dump(to_encode, f, indent="\t")

        read_info.set_hash_for_file("files/list/background.json", store.get_or_execute(ExtractBgList({
            "bg_list_hash": read_info.get_hash_and_remove("rom/MAP_BG/bg_list.dat")
        })))
    
    def on_write(self, store, write_info):
        class ReackBgList(Executer):
            UNIQUE_NAME = "json-to-bglist-1"

            def execute(self, store, hash):
                print("repacking bg_list")

                bg_list_json = None
                with open(store.get_derivation_path(self.input["bg_list_json_hash"]), "r") as f:
                    bg_list_json = json.load(f)
                
                bg_list = BgListDatHandler.deserialize(bytes(0))

                for level in bg_list_json:
                    entry = BgListEntry(
                        level["bpl"],
                        level["bpc"],
                        level["bma"],
                        level["bpas"],
                    )
                    bg_list.add_level(entry)
                
                with open(store.get_derivation_path(hash), "wb") as f:
                    f.write(BgListDatHandler.serialize(bg_list))
        
        write_info.set_hash_for_file("rom/MAP_BG/bg_list.dat", store.get_or_execute(ReackBgList({
            "bg_list_json_hash": write_info.get_hash_and_remove("files/list/background.json")
        })))

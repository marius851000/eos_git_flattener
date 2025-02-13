from skytemple_files.list.object.handler import ObjectListBinHandler
import json
from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer
from skytemple_files.common.ppmdu_config.script_data import Pmd2ScriptObject

class FileAnalyserObjectBin(FileAnalyserBase):
    
    def on_read(self, store, read_info):
        class ObjectBinDecoder(Executer):
            UNIQUE_NAME = "obj-bin-dec-3"

            def execute(self, store, hash):
                print("Extracting object bin file")

                obj_bin_bytes = None
                with open(store.get_derivation_path(self.input["object_bin_hash"]), "rb") as f:
                    obj_bin_bytes = f.read()

                obj_bin = ObjectListBinHandler.deserialize(obj_bin_bytes)

                result = []
                for entry in obj_bin.list:
                    result.append({
                        "id": entry.id,
                        "unk1": entry.unk1,
                        "unk2": entry.unk2,
                        "unk3": entry.unk3,
                        "name": entry.name
                    })
                
                with open(store.get_derivation_path(hash), "w") as f:
                    json.dump(result, f, indent="\t")
        
        obj_bin_source_hash = read_info.get_hash_and_remove("rom/BALANCE/objects.bin")

        obj_bin_json_hash = store.get_or_execute(ObjectBinDecoder({
            "object_bin_hash": obj_bin_source_hash
        }))

        read_info.set_hash_for_file("files/list/objects.json", obj_bin_json_hash)
    
    def on_write(self, store, write_info):
        class ObjectBinEncoder(Executer):
            UNIQUE_NAME = "obj-bin-enc-1"

            def execute(self, store, hash):
                print("repacking objects.bin")

                json_source = None
                with open(store.get_derivation_path(self.input["objects_json_hash"]), "r") as f:
                    json_source = json.load(f)
                
                obj_bin = ObjectListBinHandler.deserialize(bytes(0))

                for entry in json_source:
                    obj_bin.list.append(
                        Pmd2ScriptObject(
                            entry["id"],
                            entry["unk1"],
                            entry["unk2"],
                            entry["unk3"],
                            entry["name"]
                        )
                    )

                out_bytes = ObjectListBinHandler.serialize(obj_bin)

                with open(store.get_derivation_path(hash), "wb") as f:
                    f.write(out_bytes)
        
        obj_json_hash = write_info.get_hash_and_remove("files/list/objects.json")

        obj_bin_hash = store.get_or_execute(ObjectBinEncoder({
            "objects_json_hash": obj_json_hash
        }))

        write_info.set_hash_for_file("rom/BALANCE/objects.bin", obj_bin_hash)
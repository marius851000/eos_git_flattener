from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer
from skytemple_files.data.data_cd.handler import DataCDHandler
import os
import json

PATHS = [
    # should not end with a /
    ["rom/BALANCE/process.bin", "code/sp"],
    ["rom/BALANCE/waza_cd.bin", "code/moves"],
    ["rom/BALANCE/item_cd.bin", "code/items"]
]

class FileAnalyserDataCD(FileAnalyserBase):

    def on_read(self, store, read_info):
        class ExtractDataCd(Executer):
            UNIQUE_NAME = "data-cd-ext-2"

            def execute(self, store, hash):
                print("extracting some code")
                b = None
                with open(store.get_derivation_path(self.input["input_hash"]), "rb") as f:
                    b = f.read()
                
                data_cd = DataCDHandler.deserialize(b)
                
                out_base = store.get_derivation_path(hash)
                os.makedirs(out_base)

                for effect_code_id in range(len(data_cd.effects_code)):
                    this_one_out_path = os.path.join(out_base, str(effect_code_id) + ".bin")
                    with open(this_one_out_path, "wb") as f:
                        f.write(data_cd.effects_code[effect_code_id])
                
                with open(os.path.join(out_base, "link.json"), "w") as f:
                    json.dump(data_cd.items_effects, f, indent="\t")
        
        for file_path in PATHS:
            read_info.set_hash_for_file(file_path[1], store.get_or_execute(ExtractDataCd({
                "input_hash": read_info.get_hash_and_remove(file_path[0])
            })))
    
    def on_write(self, store, write_info):

        class DataCdRepack(Executer):
            UNIQUE_NAME = "data-cd-re-1"

            def execute(self, store, hash):
                print("writing a code file")
                
                data_cd_base = DataCDHandler.deserialize(bytes([4, 0, 0, 0, 4, 0, 0, 0]))
                
                for i in self.input["input_files"]:
                    input_file_hash = self.input["input_files"][i]

                    if i.endswith(".bin"):
                        nb = int(i.split(".")[0])
                        while len(data_cd_base.effects_code) <= nb:
                            data_cd_base.effects_code.append(None)

                        input_file_bytes = None
                        with open(store.get_derivation_path(input_file_hash), "rb") as f:
                            input_file_bytes = f.read()
                        data_cd_base.effects_code[nb] = input_file_bytes
                    elif i.endswith(".json"):
                        decoded = None
                        with open(store.get_derivation_path(input_file_hash), "r") as f:
                            decoded = json.load(f)
                        data_cd_base.items_effects = decoded
                
                out_bytes = DataCDHandler.serialize(data_cd_base)
                
                with open(store.get_derivation_path(hash), "wb") as f:
                    f.write(out_bytes)

        for file_path in PATHS:
            found = []
            data = {}

            for path in write_info.path_to_hash:
                if path.startswith(file_path[1]):
                    found.append(path)
            
            for path in found:
                hash = write_info.get_hash_and_remove(path)
                name = path.split("/")[-1]
                data[name] = hash
            
            write_info.set_hash_for_file(file_path[0], store.get_or_execute(DataCdRepack({
                "input_files": data
            })))

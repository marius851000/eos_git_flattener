from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer
from skytemple_files.container.bin_pack.model import BinPack
from skytemple_files.container.bin_pack.writer import BinPackWriter
import os

PATHS = [
    # should not end with a /
    ["rom/MONSTER/m_attack.bin", "sprites/attack"],
    ["rom/MONSTER/m_ground.bin", "sprites/ground"],
    ["rom/MONSTER/monster.bin", "sprites/monster"]
]

class FileAnalyserBinPack(FileAnalyserBase):

    def on_read(self, store, read_info):
        class BinPackUnpack(Executer):
            UNIQUE_NAME = "binpack-dec-1"

            def execute(self, store, hash):
                b = None
                with open(store.get_derivation_path(self.input["input_hash"]), "rb") as f:
                    b = f.read()
                pack = BinPack(b)
                
                out_base = store.get_derivation_path(hash)
                os.makedirs(out_base)

                for file_pos in range(len(pack)):
                    this_one_out_path = os.path.join(out_base, str(file_pos) + ".bin")
                    with open(this_one_out_path, "wb") as f:
                        f.write(pack[file_pos])
        
        for file_path in PATHS:
            read_info.set_hash_for_file(file_path[1], store.get_or_execute(BinPackUnpack({
                "input_hash": read_info.get_hash_and_remove(file_path[0])
            })))
    
    def on_write(self, store, write_info):
        class BinPackRepack(Executer):
            UNIQUE_NAME = "binpack-re-1"

            def execute(self, store, hash):
                print("writing a bin pack")
                pack_base = BinPack(bytes([0] * 4))
                
                for i in range(len(self.input["input_files"])):
                    input_file_hash = self.input["input_files"][str(i)]
                    input_file_bytes = None
                    with open(store.get_derivation_path(input_file_hash), "rb") as f:
                        input_file_bytes = f.read()
                    
                    pack_base.append(input_file_bytes)
                
                out_bytes = BinPackWriter(pack_base, 0x1300).write()
                
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
                pos = path.split("/")[-1].split(".")[0]
                data[str(int(pos))] = hash
            
            write_info.set_hash_for_file(file_path[0], store.get_or_execute(BinPackRepack({
                "input_files": data
            })))

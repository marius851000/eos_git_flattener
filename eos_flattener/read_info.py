from ndspy import rom
import os
from eos_flattener.file_tool import copy_recursively
import subprocess
import shutil

class ReadInfo:
    def __init__(self, rom_path, store, temp_dir):
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        self.store = store
        self.path_to_hash = {

        }

        rom_data = rom.NintendoDSRom.fromFile(rom_path)
        for i, file in enumerate(rom_data.files):
            file_name = rom_data.filenames.filenameOf(i)
            if file_name != None:
                self.path_to_hash["rom/" + file_name] = store.add_byte(file)

        
        os.makedirs(temp_dir, exist_ok=False)
        subprocess.check_call([
            "ndstool",
            "-x", rom_path,
            "-9", os.path.join(temp_dir, "arm9.bin"),
            "-7", os.path.join(temp_dir, "arm7.bin"),
            "-y9", os.path.join(temp_dir, "y9.bin"),
            "-y7", os.path.join(temp_dir, "y7.bin"),
            "-y", os.path.join(temp_dir, "overlay"),
            "-t", os.path.join(temp_dir, "banner.bin"),
            "-h", os.path.join(temp_dir, "header.bin"),
        ])

        self.path_to_hash["code/arm9.bin"] = store.add_file(os.path.join(temp_dir, "arm9.bin"))
        self.path_to_hash["code/arm7.bin"] = store.add_file(os.path.join(temp_dir, "arm7.bin"))
        self.path_to_hash["code/y9.bin"] = store.add_file(os.path.join(temp_dir, "y9.bin"))
        self.path_to_hash["code/y7.bin"] = store.add_file(os.path.join(temp_dir, "y7.bin"))
        self.path_to_hash["code/banner.bin"] = store.add_file(os.path.join(temp_dir, "banner.bin"))
        self.path_to_hash["code/header.bin"] = store.add_file(os.path.join(temp_dir, "header.bin"))

        for overlay_file_name in os.listdir(os.path.join(temp_dir, "overlay")):
            overlay_path = os.path.join(temp_dir, "overlay", overlay_file_name)
            self.path_to_hash["code/overlay/" + overlay_file_name] = store.add_file(overlay_path)
        
        
    
    def get_hash_and_remove(self, path):
        v = self.path_to_hash[path]
        del self.path_to_hash[path]
        return v

    def run_analyzers(self, analyzers):
        for analyzer in analyzers:
            analyzer.on_read(self.store, self)
    
    def set_hash_for_file(self, path, hash):
        self.path_to_hash[path] = hash
    
    def dump_data(self, path):
        os.makedirs(path, exist_ok=True)
        for file_path in self.path_to_hash:
            file_source_path = self.store.get_derivation_path(self.path_to_hash[file_path])
            file_path_concat = os.path.join(path, file_path)
            os.makedirs(os.path.dirname(file_path_concat), exist_ok=True)
            copy_recursively(file_source_path, file_path_concat)

    

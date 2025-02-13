import os
import shutil
from eos_flattener.file_tool import copy_recursively
import subprocess

class WriteInfo:
    def __init__(self, root, store):

        self.root = root
        self.store = store

        self.path_to_hash = {

        }
        
        for (dirpath, dirnames, filenames) in os.walk(self.root):
            for file_name in filenames:
                file_path = os.path.join(dirpath, file_name)
                file_path_rel = os.path.relpath(file_path, self.root)
                self.path_to_hash[file_path_rel] = store.add_file(file_path)
    
    def run_analyzers(self, analyzers):
        for analyzer in analyzers:
            analyzer.on_write(self.store, self)
    
    def set_hash_for_file(self, path, hash):
        self.path_to_hash[path] = hash
    
    def get_hash_and_remove(self, path):
        hash = self.path_to_hash[path]
        del self.path_to_hash[path]
        return hash
    
    def write_rom(self, target_file, temp_folder):
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

        os.makedirs(temp_folder, exist_ok=False)
        for file_path_rel in self.path_to_hash:
            file_path_source = self.store.get_derivation_path(self.path_to_hash[file_path_rel])

            if file_path_rel.startswith("rom"):
                file_path_dest = os.path.join(temp_folder, file_path_rel)
                os.makedirs(os.path.dirname(file_path_dest), exist_ok=True)
                copy_recursively(file_path_source, file_path_dest)

            if file_path_rel.startswith("code/overlay"):
                file_path_dest = os.path.join(temp_folder, file_path_rel)
                os.makedirs(os.path.dirname(file_path_dest), exist_ok=True)
                copy_recursively(file_path_source, file_path_dest)
        
        subprocess.check_call([
            "ndstool", "-c", target_file,
            "-9", self.store.get_derivation_path(self.path_to_hash["code/arm9.bin"]),
            "-7", self.store.get_derivation_path(self.path_to_hash["code/arm7.bin"]),
            "-y9", self.store.get_derivation_path(self.path_to_hash["code/y9.bin"]),
            "-y7", self.store.get_derivation_path(self.path_to_hash["code/y7.bin"]),
            "-h", self.store.get_derivation_path(self.path_to_hash["code/header.bin"]),
            "-t", self.store.get_derivation_path(self.path_to_hash["code/banner.bin"]),
            "-h", self.store.get_derivation_path(self.path_to_hash["code/header.bin"]),
            "-y", os.path.join(temp_folder, "code/overlay"),
            "-d", os.path.join(temp_folder, "rom")
        ])



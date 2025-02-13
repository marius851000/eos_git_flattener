# Extract SSB, SSA, SSE and lsd

from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer
from hashlib import sha256
import shutil
from skytemple_files.common.ppmdu_config.xml_reader import Pmd2XmlReader
from skytemple_files.script.ssb.handler import SsbHandler
import os
from skytemple_files.script.ssb.script_compiler import ScriptCompiler
from skytemple_files.common import string_codec

#TODO: is kinda unfinished, but can still work if you don’t mind re-decompiling the scripts
class FileAnalyserScript(FileAnalyserBase):
    def __init__(self, version):
        super().__init__()
        self.version = version

    def on_read(self, store, read_info):
        class SsbScriptExtract(Executer):
            UNIQUE_NAME = "ssb-to-exps-1"

            def execute(self, store, hash):
                print("extracting ssb " + self.input["source"])
                source_path = store.get_derivation_path(self.input["source"])
                f = open(source_path, "rb")
                b = f.read()
                f.close()

                static_data = Pmd2XmlReader.load_default(for_version=self.input["version"])
                
                try:
                    ssb = SsbHandler.deserialize(b, static_data)
                    explorer_script, _ = ssb.to_explorerscript()
                except Exception as e:
                    print("error during decompilation")
                    explorer_script = "Failed to decompile"
                
                f = open(store.get_derivation_path(hash), "w")
                f.write(explorer_script)
                f.close()


        class ScriptFolderMaker(Executer):
            UNIQUE_NAME = "script-folder-2"
            #TODO: also manage lsd

            def execute(self, store, hash):
                print("extracting a script folder")
                files = self.input["files"].copy()

                managed_files = []
                new_files = {}

                for file_path, file_hash in files.items():
                    if file_path.endswith(".ssb"):
                        managed_files.append(file_path)
                        source_hash = store.get_or_execute(SsbScriptExtract({
                            "source": file_hash,
                            "version": self.input["version"]
                        }))
                        new_files[file_path[:-4] + ".exps"] = source_hash
                        new_files[file_path[:-4] + ".original.ssb"] = file_hash
                        source_bytes = None
                        with open(store.get_derivation_path(source_hash), "rb") as source_file:
                            source_bytes = source_file.read()
                        source_hasher = sha256()
                        source_hasher.update(source_bytes)
                        new_files[file_path[:-4] + '.exps.srchash'] = store.add_byte(source_hasher.hexdigest().encode("utf-8"))
                
                for managed_path in managed_files:
                    del files[managed_path]
                
                for new_file_path, new_file_hash in new_files.items():
                    files[new_file_path] = new_file_hash
                
                out_folder = store.get_derivation_path(hash)
                os.makedirs(out_folder, exist_ok=False)

                for file_path, file_hash in files.items():
                    shutil.copy(store.get_derivation_path(file_hash), os.path.join(out_folder, file_path))
        
        script_files = {}

        file_to_remove = []
        for path, hash in read_info.path_to_hash.items():
            if path.startswith("rom/SCRIPT/"):
                folder_name = path.split("/")[2]
                if folder_name not in script_files:
                    script_files[folder_name] = {}
                
                script_files[folder_name][path.split("/")[3]] = hash
        
        #TODO: does not appear to work...
        for to_remove in file_to_remove:
            del read_info.path_to_hash[to_remove]
        
        for folder_name, files in script_files.items():
            read_info.path_to_hash["files/script/" + folder_name] = store.get_or_execute(ScriptFolderMaker({
                "files": files,
                "version": self.version
            }))
            
    
    def on_write(self, store, write_info):
        class SsbScriptRepackFromExtract(Executer):
            UNIQUE_NAME = "exps-to-ssb-ext-1"
            def execute(self, store, hash):
                print("compiling exps " + self.input["source"])
                string_codec.init()

                source_path = store.get_derivation_path(self.input["source"])

                f = open(source_path, "r")
                c = f.read()
                f.close()

                static_data = Pmd2XmlReader.load_default(for_version=self.input["version"])
                compiler = ScriptCompiler(static_data)
                ssb, _ = compiler.compile_explorerscript(
                    c, source_path
                )

                ssb_bytes = SsbHandler().serialize(ssb, static_data)

                f = open(store.get_derivation_path(hash), "wb")
                f.write(ssb_bytes)
                f.close()


        class ScriptFolderFromExtract(Executer):
            UNIQUE_NAME = "script-folder-ext-4"
            def execute(self, store, hash):
                print("repacking a script folder")

                files = self.input["files"].copy()

                managed_files = []
                new_files = {}

                for file_path, file_hash in files.items():
                    if file_path.endswith(".exps"):
                        original_ssb_path = file_path[:-5] + ".original.ssb"
                        original_ssb_store_hash = files.get(original_ssb_path)
                        source_original_hash_path = file_path[:-5] + ".exps.srchash"
                        source_original_hash_store_hash = files.get(source_original_hash_path)

                        source_original_hash = None
                        with open(store.get_derivation_path(source_original_hash_store_hash), "r") as f:
                            source_original_hash = f.read()
                        
                        source_current_bytes = None
                        with open(store.get_derivation_path(file_hash), "rb") as f:
                            source_current_bytes = f.read()
                        
                        source_hasher = sha256()
                        source_hasher.update(source_current_bytes)
                        calculated_source_hash = source_hasher.hexdigest()

                        if calculated_source_hash == source_original_hash:
                            new_files[file_path[:-5] + ".ssb"] = original_ssb_store_hash
                        else:
                            new_files[file_path[:-5] + ".ssb"] = store.get_or_execute(SsbScriptRepackFromExtract({
                                "source": file_hash,
                                "version": self.input["version"]
                            }))
                        managed_files.append(file_path)
                        managed_files.append(source_original_hash_path)
                        managed_files.append(original_ssb_path)
                
                for managed_path in managed_files:
                    del files[managed_path]
                
                for new_file_path, new_file_hash in new_files.items():
                    files[new_file_path] = new_file_hash
                
                out_folder = store.get_derivation_path(hash)
                os.makedirs(out_folder, exist_ok=False)

                for file_path, file_hash in files.items():
                    shutil.copy(store.get_derivation_path(file_hash), os.path.join(out_folder, file_path))

        script_files = {}
        file_to_remove = []

        for path, hash in write_info.path_to_hash.items():
            if path.startswith("files/script/"):
                folder_name = path.split("/")[2]
                if folder_name not in script_files:
                    script_files[folder_name] = {}
                
                script_files[folder_name][path.split("/")[3]] = hash
        
        for to_remove in file_to_remove:
            del write_info.path_to_hash[to_remove]
        
        for folder_name, files in script_files.items():
            write_info.path_to_hash["rom/SCRIPT/" + folder_name] = store.get_or_execute(ScriptFolderFromExtract({
                "files": files,
                "version": self.version
            }))
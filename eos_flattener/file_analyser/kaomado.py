from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer
from skytemple_rust.st_kao import Kao
from skytemple_rust.st_kao import KaoWriter
import os
from PIL import Image

class FileAnalyserKaomado(FileAnalyserBase):

    def on_read(self, store, read_info):
        class KaoExtender(Executer):
            UNIQUE_NAME = "kao-3"

            def execute(self, store, hash):
                print("extracting portraits")
                f = open(store.get_derivation_path(self.input["kaomado_file"]), "rb")
                b = f.read()
                f.close()

                kao = Kao(b)
                dest_dir = store.get_derivation_path(hash)
                os.makedirs(dest_dir, exist_ok=True)

                #default_portrait_base = kao.get(0, 0)
                
                for (index, subindex, image) in kao:
                    if image != None:# and image != default_portrait_base:
                        portrait_dir = os.path.join(dest_dir, str(index))
                        os.makedirs(portrait_dir, exist_ok=True)
                        single_portrait_file = os.path.join(portrait_dir, str(subindex) + ".bmp")
                        image.get().save(single_portrait_file)

        kaomado_hash = read_info.get_hash_and_remove("rom/FONT/kaomado.kao")

        kaomado_extracted_hash = store.get_or_execute(KaoExtender({
            "kaomado_file": kaomado_hash
        }))

        read_info.set_hash_for_file("files/portraits", kaomado_extracted_hash)
    
    def on_write(self, store, write_info):
        class KaoExtenderFromExtract(Executer):
            UNIQUE_NAME = "kao-ext-2"

            def execute(self, store, hash):
                print("generating kaomado.kao")

                latest = 0
                for monster_id in self.input["portraits"]:
                    if int(monster_id) > latest:
                        latest = int(monster_id)
                
                kao = Kao.create_new(latest + 1)
                for monster_id, monster_dict in self.input["portraits"].items():
                    for portrait_id, portrait_hash in monster_dict.items():
                        image = Image.open(store.get_derivation_path(portrait_hash))
                        kao.set_from_img(int(monster_id), int(portrait_id), image)
                
                #for entry_id in range(1, latest):
                #    has_any = False
                #    for i in range(40):
                #        if kao.get(entry_id, i) != None:
                #            has_any = True
                #    if not has_any:
                #        for i in range(40):
                #            current = kao.get(0, i)
                #            if current != None:
                #                kao.set(entry_id, i, current)
                
                writer = KaoWriter()
                data = writer.write(kao)

                f = open(store.get_derivation_path(hash), "wb")
                f.write(data)
                f.close()
        
        kaomado_source = {}
        to_remove_post = []

        for file_path in write_info.path_to_hash:
            if file_path.startswith("files/portraits"):
                monster_id = file_path.split("/")[2]
                portrait_id = file_path.split("/")[3].split(".")[0]
                if monster_id not in kaomado_source:
                    kaomado_source[monster_id] = {}
                kaomado_source[monster_id][portrait_id] = write_info.path_to_hash[file_path]
                to_remove_post.append(file_path)
        
        for file_path_to_remove in to_remove_post:
            del write_info.path_to_hash[file_path_to_remove]
        
        write_info.path_to_hash["rom/FONT/kaomado.kao"] = store.get_or_execute(KaoExtenderFromExtract({
            "portraits": kaomado_source
        }))
    
    
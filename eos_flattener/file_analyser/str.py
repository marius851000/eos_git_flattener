from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer
from skytemple_files.data.str.handler import StrHandler
import json
from skytemple_files.common import string_codec
from skytemple_files.common.ppmdu_config.xml_reader import Pmd2XmlReader
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import normalize_string
from skytemple_files.data.val_list.handler import ValListHandler

def read_str(path):
    b = None
    with open(path, "rb") as f:
        b = f.read()
    return StrHandler.deserialize(b)
        
class FileAnalyserStr(FileAnalyserBase):

    def __init__(self, game_version):
        self.game_version = game_version
        super().__init__()

    def on_read(self, store, read_info):
        class ExtractStr(Executer):
            UNIQUE_NAME = "str-ext-1"

            def execute(self, store, hash):
                print("Extracting an str")
                
                str_cont = read_str(store.get_derivation_path(self.input["str_hash"]))

                with open(store.get_derivation_path(hash), "w") as f:
                    json.dump(str_cont.strings, f, indent="\t")
        
        matched = []

        for path in read_info.path_to_hash:
            if path.startswith("rom/MESSAGE/") and path.endswith(".str"):
                matched.append(path)
        
        for match in matched:
            print(match)
            dest_path = "files/message/" + match.split("/")[-1].split(".")[0] + ".json"
            read_info.set_hash_for_file(dest_path, store.get_or_execute(ExtractStr({
                "str_hash": read_info.get_hash_and_remove(match)
            })))
            

            lang_letter = dest_path.split("_")[-1].split(".")[0]
            if self.game_version == "EoS_EU":
                read_info.get_hash_and_remove("rom/BALANCE/st_n2m_" + lang_letter + ".bin")
                read_info.get_hash_and_remove("rom/BALANCE/st_m2n_" + lang_letter + ".bin")
        
    def on_write(self, store, read_info):
        def get_name_result(model):
            ppmdu_config = Pmd2XmlReader.load_default(self.game_version)
            pokemon_name_block = ppmdu_config.string_index_data.string_blocks["Pokemon Names"]
            pre_sorted_list = list(enumerate(model.strings[pokemon_name_block.begin:pokemon_name_block.begin+FileType.MD.properties().num_entities]))
            pre_sorted_list.sort(key=lambda x: normalize_string(x[1]))
            sorted_list = [x[0] for x in pre_sorted_list]
            inv_sorted_list = [sorted_list.index(i) for i in range(FileType.MD.properties().max_possible)]

            return (sorted_list, inv_sorted_list)

        class RepackStr(Executer):
            UNIQUE_NAME = "str-enc-1"

            def execute(self, store, hash):
                print("Repacking an str")
                string_codec.init()

                decoded = None
                with open(store.get_derivation_path(self.input["str_json_hash"]), "r") as f:
                    decoded = json.load(f)
                
                str_cont = StrHandler.deserialize(bytes(0))
                str_cont.strings = decoded

                with open(store.get_derivation_path(hash), "wb") as f:
                    f.write(StrHandler.serialize(str_cont))
        
        class GenerateN2M(Executer):
            UNIQUE_NAME = "n2m-gen-1"

            def execute(self, store, hash):
                print("creating an n2m")
                string_codec.init()

                model = read_str(store.get_derivation_path(self.input["str_hash"]))

                (sorted_list, inv_sorted_list) = get_name_result(model)

                n2m = ValListHandler.deserialize(bytes(0))
                n2m.set_list(sorted_list)
                with open(store.get_derivation_path(hash), "wb") as f:
                    f.write(ValListHandler.serialize(n2m))
        
        class GenerateM2N(Executer):
            UNIQUE_NAME = "m2n-gen-1"

            def execute(self, store, hash):
                print("creating an m2n")
                string_codec.init()

                model = read_str(store.get_derivation_path(self.input["str_hash"]))

                (sorted_list, inv_sorted_list) = get_name_result(model)

                m2n = ValListHandler.deserialize(bytes(0))
                m2n.set_list(inv_sorted_list)
                with open(store.get_derivation_path(hash), "wb") as f:
                    f.write(ValListHandler.serialize(m2n))
        
                
        matched = []

        for path in read_info.path_to_hash:
            if path.startswith("files/message/") and path.endswith(".json"):
                matched.append(path)
        
        for match in matched:
            dest_path = "rom/MESSAGE/" + match.split("/")[-1].split(".")[0] + ".str"
            str_hash = store.get_or_execute(RepackStr({
                "str_json_hash": read_info.get_hash_and_remove(match)
            }))
            read_info.set_hash_for_file(dest_path, str_hash)

            if self.game_version == "EoS_EU":
                lang_letter = dest_path.split("_")[-1].split(".")[0]
                read_info.set_hash_for_file("rom/BALANCE/st_n2m_" + lang_letter + ".bin", store.get_or_execute(GenerateN2M({
                    "str_hash": str_hash
                })))
                read_info.set_hash_for_file("rom/BALANCE/st_m2n_" + lang_letter + ".bin", store.get_or_execute(GenerateM2N({
                    "str_hash": str_hash
                })))


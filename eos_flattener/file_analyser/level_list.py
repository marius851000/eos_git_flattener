
from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer, ToJsonExecuterTemplate, JsonToBytesExecuterTemplate
from skytemple_files.list.level.model import LevelListBin
from skytemple_files.container.sir0.handler import Sir0Handler
from skytemple_files.common.ppmdu_config.script_data import Pmd2ScriptLevel

class FileAnalyserLevelList(FileAnalyserBase):
    def on_read(self, store, read_info):
        class DecodeLevelList(ToJsonExecuterTemplate):
            UNIQUE_NAME = "level-list-dec-1"

            def to_json(self, bytes):
                print("decoding level_list")

                level_list = Sir0Handler.unwrap_obj(
                    Sir0Handler.deserialize(bytes), LevelListBin
                )

                r = []
                for entry in level_list.list:
                    r.append({
                        "id": entry.id,
                        "mapid": entry.mapid,
                        "name": entry.name,
                        "mapty": entry.mapty,
                        "nameid": entry.nameid,
                        "weather": entry.weather
                    })
                
                return r

        level_list_source_hash = read_info.get_hash_and_remove("rom/BALANCE/level_list.bin")

        read_info.set_hash_for_file("files/list/level_list.json", store.get_or_execute(DecodeLevelList({
            "binary_input_hash": level_list_source_hash
        })))
    
    def on_write(self, store, write_info):
        class EncodeLevelList(JsonToBytesExecuterTemplate):
            UNIQUE_NAME = "level-list-enc-2"

            def to_bytes(self, content):
                r = []
                for entry in content:
                    r.append(Pmd2ScriptLevel(
                        id = entry["id"],
                        mapid = entry["mapid"],
                        name = entry["name"],
                        mapty = entry["mapty"],
                        nameid = entry["nameid"],
                        weather = entry["weather"]
                    ))

                level_list = LevelListBin(b"\xaa" * 12, 0)
                level_list.list = r
                return Sir0Handler.serialize(Sir0Handler.wrap_obj(level_list))
        
        write_info.set_hash_for_file("rom/BALANCE/level_list.bin", store.get_or_execute(EncodeLevelList({
            "json_input_hash": write_info.get_hash_and_remove("files/list/level_list.json")
        })))

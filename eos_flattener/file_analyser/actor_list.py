from .file_analyser_base import FileAnalyserBase
from skytemple_files.container.sir0.handler import Sir0Handler
from skytemple_files.list.actor.model import ActorListBin
from eos_flattener.executer import Executer
from skytemple_files.common.ppmdu_config.script_data import Pmd2ScriptEntity
import json

class FileAnalyzerActorListBin(FileAnalyserBase):

    def on_read(self, store, read_info):
        class ActorListBinDecoder(Executer):
            UNIQUE_NAME = "actor-list-bin-dec-2"

            def execute(self, store, hash):
                print("extracting actor_list.bin")
                f = open(store.get_derivation_path(self.input["actor_list_hash"]), "rb")
                b = f.read()
                f.close()

                actor_list = Sir0Handler.unwrap_obj(
                    Sir0Handler.deserialize(b), ActorListBin
                )

                list_to_write = []
                cur_id = 0
                for actor in actor_list.list:
                    list_to_write.append({
                        "id": actor.id,
                        "entid": actor.entid,
                        "name": actor.name,
                        "type": actor.type,
                        "unk3": actor.unk3,
                        "unk4": actor.unk4
                    })
                    assert(actor.id == cur_id)
                    cur_id += 1
                
                f = open(store.get_derivation_path(hash), "w")
                json.dump(list_to_write, f, indent="\t")
                f.close()
        
        actor_list_hash = read_info.get_hash_and_remove("rom/BALANCE/actor_list.bin")

        actor_list_extract_hash = store.get_or_execute(ActorListBinDecoder({
            "actor_list_hash": actor_list_hash
        }))

        read_info.set_hash_for_file("files/list/actor_list.json", actor_list_extract_hash)
    
    def on_write(self, store, write_info):
        class ActorListBinEncoder(Executer):
            UNIQUE_NAME = "actor-list-bin-enc-1"

            def execute(self, store, hash):
                print("repacking actor_list.bin")
                f = open(store.get_derivation_path(self.input["actor_list_json_hash"]))
                actor_list_dict = json.load(f)
                f.close()

                actor_list_enc = []
                for actor_dict in actor_list_dict:
                    actor_list_enc.append(Pmd2ScriptEntity(
                        id=actor_dict["id"],
                        type=actor_dict["type"],
                        entid=actor_dict["entid"],
                        name=actor_dict["name"],
                        unk3=actor_dict["unk3"],
                        unk4=actor_dict["unk4"],
                    ))
                
                list_data = ActorListBin(bytes([0, 0, 0, 0]), 0) # ugly hack for the fact there is no null constructor

                list_data.list = actor_list_enc

                bin = Sir0Handler.serialize(Sir0Handler.wrap_obj(list_data))

                f = open(store.get_derivation_path(hash), "wb")
                f.write(bin)
                f.close()
        
        actor_list_json_hash = write_info.get_hash_and_remove("files/list/actor_list.json")

        actor_list_bin_hash = store.get_or_execute(ActorListBinEncoder({
            "actor_list_json_hash": actor_list_json_hash
        }))

        write_info.set_hash_for_file("rom/BALANCE/actor_list.bin", actor_list_bin_hash)
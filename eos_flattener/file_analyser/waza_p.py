from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer
from skytemple_files.data.waza_p.handler import WazaPHandler
from skytemple_files.data.waza_p._model import WazaP, WazaMove, MoveLearnset, LevelUpMove, WazaMoveRangeSettings
import json

class FileAnalyserWazaP(FileAnalyserBase):
    def on_read(self, store, read_info):
        class WazaPToJson(Executer):
            UNIQUE_NAME = "wazap-to-json-2"

            def execute(self, store, hash):
                print("converting a wazap to json")

                wazap_bytes = None
                with open(store.get_derivation_path(self.input["wazap_hash"]), "rb") as f:
                    wazap_bytes = f.read()
                
                wazap = WazaPHandler.deserialize(wazap_bytes)

                result = {
                    "moves": [],
                    "learnsets": []
                }

                def range_to_dict(range):
                    return {
                        "target": range.target,
                        "range": range.range,
                        "condition": range.condition,
                        "unused": range.unused
                    }

                for move in wazap.moves:
                    move_json = {
                        "base_power": move.base_power,
                        "type": move.type,
                        "category": move.category,
                        "settings_range": range_to_dict(move.settings_range),
                        "settings_range_ai": range_to_dict(move.settings_range_ai),
                        "base_pp": move.base_pp,
                        "ai_weight": move.ai_weight,
                        "miss_accuracy": move.miss_accuracy,
                        "accuracy": move.accuracy,
                        "ai_condition1_chance": move.ai_condition1_chance,
                        "number_chained_hits": move.number_chained_hits,
                        "max_upgrade_level": move.max_upgrade_level,
                        "crit_chance": move.crit_chance,
                        "affected_by_magic_coat": move.affected_by_magic_coat,
                        "is_snatchable": move.is_snatchable,
                        "uses_mouth": move.uses_mouth,
                        "ai_frozen_check": move.ai_frozen_check,
                        "ignores_taunted": move.ignores_taunted,
                        "range_check_text": move.range_check_text,
                        "move_id": move.move_id,
                        "message_id": move.message_id
                    }
                    result["moves"].append(move_json)
                
                for learnset in wazap.learnsets:
                    level_up_moves_json = []
                    for level_up_move in learnset.level_up_moves:
                        level_up_moves_json.append({
                            "move_id": level_up_move.move_id,
                            "level_id": level_up_move.level_id
                        })
                    
                    learnset_json = {
                        "egg_moves": learnset.egg_moves,
                        "tm_hm_moves": learnset.tm_hm_moves,
                        "level_up_moves": level_up_moves_json
                    }
                    result["learnsets"].append(learnset_json)

                with open(store.get_derivation_path(hash), "w") as f:
                    json.dump(result, f, indent="\t")
        
        read_info.set_hash_for_file("files/list/moves_1.json", store.get_or_execute(WazaPToJson({
            "wazap_hash": read_info.get_hash_and_remove("rom/BALANCE/waza_p.bin")
        })))
        read_info.set_hash_for_file("files/list/moves_2.json", store.get_or_execute(WazaPToJson({
            "wazap_hash": read_info.get_hash_and_remove("rom/BALANCE/waza_p2.bin")
        })))
    
    def on_write(self, store, write_info):
        class JsonToWazaP(Executer):
            UNIQUE_NAME = "json-to-wazap-1"

            def execute(self, store, hash):
                print("converting json to wazap")

                wazap = WazaP(bytes(0), 0)

                wazap_json = None
                with open(store.get_derivation_path(self.input["wazap_json_hash"]), "r") as f:
                    wazap_json = json.load(f)

                def dict_to_range(dict):
                    nb = (dict["unused"] << 12) + (dict["condition"] << 8) + (dict["range"] << 4) + dict["target"]
                    return WazaMoveRangeSettings(bytes([
                        int(nb % 256),
                        int(nb / 256)
                    ]))

                for movej in wazap_json["moves"]:
                    moveb = WazaMove(bytes(100))
                    moveb.base_power = movej["base_power"]
                    moveb.type = movej["type"]
                    moveb.category = movej["category"]
                    moveb.settings_range = dict_to_range(movej["settings_range"])
                    moveb.settings_range_ai = dict_to_range(movej["settings_range_ai"])
                    moveb.base_pp = movej["base_pp"]
                    moveb.ai_weight = movej["ai_weight"]
                    moveb.miss_accuracy = movej["miss_accuracy"]
                    moveb.accuracy = movej["accuracy"]
                    moveb.ai_condition1_chance = movej["ai_condition1_chance"]
                    moveb.number_chained_hits = movej["number_chained_hits"]
                    moveb.max_upgrade_level = movej["max_upgrade_level"]               
                    moveb.crit_chance = movej["crit_chance"]
                    moveb.affected_by_magic_coat = movej["affected_by_magic_coat"]
                    moveb.is_snatchable = movej["is_snatchable"]                 
                    moveb.uses_mouth = movej["uses_mouth"]
                    moveb.ai_frozen_check = movej["ai_frozen_check"]
                    moveb.ignores_taunted = movej["ignores_taunted"]
                    moveb.range_check_text = movej["range_check_text"]
                    moveb.move_id = movej["move_id"]
                    moveb.message_id = movej["message_id"]
                    wazap.moves.append(moveb)
                
                for learnsetj in wazap_json["learnsets"]:
                    level_up_moves = []
                    for level_up_movesj in learnsetj["level_up_moves"]:
                        level_up_moves.append(LevelUpMove(
                            level_up_movesj["move_id"],
                            level_up_movesj["level_id"]
                        ))
                    wazap.learnsets.append(MoveLearnset(
                        level_up_moves,
                        learnsetj["tm_hm_moves"],
                        learnsetj["egg_moves"]
                    ))

                
                with open(store.get_derivation_path(hash), "wb") as f:
                    f.write(WazaPHandler.serialize(wazap))
        
        write_info.set_hash_for_file("rom/BALANCE/waza_p.bin", store.get_or_execute(JsonToWazaP({
            "wazap_json_hash": write_info.get_hash_and_remove("files/list/moves_1.json")
        })))

        write_info.set_hash_for_file("rom/BALANCE/waza_p2.bin", store.get_or_execute(JsonToWazaP({
            "wazap_json_hash": write_info.get_hash_and_remove("files/list/moves_2.json")
        })))
import json
from .file_analyser_base import FileAnalyserBase
from eos_flattener.executer import Executer, ToJsonExecuterTemplate, ClearDataExecuterTemplate, JsonToBytesExecuterTemplate
from skytemple_files.common.ppmdu_config.xml_reader import Pmd2XmlReader
from skytemple_files.hardcoded.monster_sprite_data_table import HardcodedMonsterSpriteDataTable, MonsterSpriteDataTableEntry

class FileAnalyserSpriteData(FileAnalyserBase):
    def on_read(self, store, read_info):
        class DecodeArm9SpriteData(ToJsonExecuterTemplate):
            UNIQUE_NAME = "arm9-sprite-info-dec-2"

            def to_json(self, bytes):
                print("decoding sprite info")
                
                ppmdu_config = Pmd2XmlReader.load_default("EoS_EU")

                sprite_table = HardcodedMonsterSpriteDataTable.get(bytes, ppmdu_config)

                r = []
                for sprite_info in sprite_table:
                    r.append({
                        "sprite_tile_slots": sprite_info.sprite_tile_slots,
                        "unk1": sprite_info.unk1
                    })
                
                return r
            
        class ClearArm9SpriteData(ClearDataExecuterTemplate):
            UNIQUE_NAME = "arm9-sprite-info-cleared-2"

            def get_part_to_clear(self, bytes):
                config = Pmd2XmlReader.load_default("EoS_EU")
                block = config.bin_sections.arm9.data.MONSTER_SPRITE_DATA
                return (block.address, block.length)
        
        arm9_source_hash = read_info.get_hash_and_remove("code/arm9.bin")

        read_info.set_hash_for_file("code/arm9.bin", store.get_or_execute(ClearArm9SpriteData({
            "binary_input_hash": arm9_source_hash
        })))

        read_info.set_hash_for_file("files/list/sprite_data.json", store.get_or_execute(DecodeArm9SpriteData({
            "binary_input_hash": arm9_source_hash
        })))
    
    def on_write(self, store, write_info):
        class EncoderArm9SpriteData(JsonToBytesExecuterTemplate):
            UNIQUE_NAME = "arm9-sprite-info-enc-1"

            def to_bytes(self, content):
                r = []
                for sprite_info in content:
                    r.append(MonsterSpriteDataTableEntry(
                        sprite_info["sprite_tile_slots"],
                        sprite_info["unk1"]
                    ))

                ppmdu_config = Pmd2XmlReader.load_default("EoS_EU")

                arm9_bytes = None
                with open(store.get_derivation_path(self.input["arm9_hash"]), "rb") as f:
                    arm9_bytes = bytearray(f.read())
                
                HardcodedMonsterSpriteDataTable.set(
                    r,
                    arm9_bytes,
                    ppmdu_config
                )

                return arm9_bytes

        write_info.set_hash_for_file("code/arm9.bin", store.get_or_execute(EncoderArm9SpriteData({
            "json_input_hash": write_info.get_hash_and_remove("files/list/sprite_data.json"),
            "arm9_hash": write_info.get_hash_and_remove("code/arm9.bin")
        })))
import json

class Executer:
    UNIQUE_NAME = None

    def __init__(self, input):
        self.input = input
    
    def get_hash(self, store):
        assert(self.UNIQUE_NAME != None)
        return store._hash_arbitrary(json.dumps(self.input).encode("utf-8")) + "-" + self.UNIQUE_NAME

    def execute(self, store, hash):
        raise

class ToJsonExecuterTemplate(Executer):
    def to_json(self, bytes):
        """Expect dict as a result"""
        raise
    
    def execute(self, store, hash):
        bytes = None
        with open(store.get_derivation_path(self.input["binary_input_hash"]), "rb") as f:
            bytes = f.read()
        
        data = self.to_json(bytes)

        with open(store.get_derivation_path(hash), "w") as f:
            json.dump(data, f, indent="\t")

class JsonToBytesExecuterTemplate(Executer):
    def to_bytes(self, content):
        """Expect bytes as a result"""
        raise

    def execute(self, store, hash):
        content = None
        with open(store.get_derivation_path(self.input["json_input_hash"]), "r") as f:
            content = json.load(f)
        
        bytes = self.to_bytes(content)

        with open(store.get_derivation_path(hash), "wb") as f:
            f.write(bytes)

class ClearDataExecuterTemplate(Executer):
    def get_part_to_clear(self, bytes):
        """Expect tupple with start bytes, length"""
        raise
    
    def execute(self, store, hash):
        bytes = None
        with open(store.get_derivation_path(self.input["binary_input_hash"]), "rb") as f:
            bytes = bytearray(f.read())
        
        (to_clear_start, to_clear_length) = self.get_part_to_clear(bytes)

        for i in range(to_clear_length):
            bytes[to_clear_start + i] = 0

        with open(store.get_derivation_path(hash), "wb") as f:
            f.write(bytes)
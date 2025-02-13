import hashlib
from eos_flattener.executer import Executer
import os
import shutil

class Store:
    def __init__(self, store_path):
        self.store_path = store_path
        os.makedirs(self.store_path, exist_ok=True)
    
    def check_if_derivation_done(self, hash):
        return os.path.exists(self.get_done_marker_path(hash))
    
    def get_done_marker_path(self, hash):
        return os.path.join(self.store_path, hash + ".done")
    
    def get_derivation_path(self, hash):
        return os.path.join(self.store_path, hash)
    
    def _hash_bytes(self, bytes):
        m = hashlib.sha256()
        m.update(b"b")
        m.update(bytes)
        return "file-" + m.hexdigest()
    
    def _hash_arbitrary(self, bytes):
        m = hashlib.sha256()
        m.update(b"a")
        m.update(bytes)
        return m.hexdigest()
    
    def get_or_execute(self, executer):
        hash = executer.get_hash(self)
        if self.check_if_derivation_done(hash):
            return hash
        else:
            dest_path = self.get_derivation_path(hash)
            if os.path.isdir(dest_path):
                shutil.rmtree(dest_path)
            elif os.path.isfile(dest_path):
                os.remove(dest_path)
            executer.execute(self, hash)
            assert(os.path.exists(dest_path))
            a = open(self.get_done_marker_path(hash), "wb")
            a.close()
            return hash
    
    def add_byte(self, byte):
        class add_file(Executer):
            UNIQUE_NAME = "file"

            def __init__(self, byte):
                super().__init__({})
                self.byte = byte

            def get_hash(self, store):
                return store._hash_bytes(self.byte)
            
            def execute(self, store, hash):
                a = open(store.get_derivation_path(hash), "wb")
                a.write(self.byte)
                a.close()

        return self.get_or_execute(add_file(byte))
    
    def add_file(self, file_path):
        f = open(file_path, "rb")
        b = f.read()
        f.close()
        return self.add_byte(b)

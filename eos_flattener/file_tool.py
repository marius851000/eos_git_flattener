import subprocess
import os
import shutil

def copy_recursively(source_path, dest_path):
    # shutil.copyfile is faster for small stuff
    if os.path.isdir(source_path):
        subprocess.check_call(["cp", "-r", "--reflink=auto", os.path.join(source_path, "."), dest_path])
    else:
        shutil.copyfile(source_path, dest_path)
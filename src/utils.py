import re
import argparse
from os import rename, fsync
import pickle

def parseIDs(arg_value, pattern=re.compile(r"^.*_.*$")):
    if pattern.match(arg_value):
        raise argparse.ArgumentTypeError("Provided ID can't have an \"_\".")
    return arg_value

def atomic_write(file_path, data):
    # see http://stackoverflow.com/questions/7433057/is-rename-without-fsync-safe
    tmp_file = f"{file_path}_tmp"  
    with open(tmp_file, "wb") as file:
        pickle.dump(data, file)
        file.flush()
        fsync(file.fileno())
      
    rename(tmp_file, file_path) # Atomic instruction

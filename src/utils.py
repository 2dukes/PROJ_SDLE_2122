from genericpath import exists
import re
import argparse
from os.path import exists
from os import rename, fsync
import pickle
import sys

def parseIDs(arg_value, pattern=re.compile(r"^.*_.*$")):
    if pattern.match(arg_value):
        raise argparse.ArgumentTypeError("Provided ID can't have an \"_\".")
    return arg_value

def atomic_write(file_path, data):
    tmp_file = f"{file_path}_tmp"  
    with open(tmp_file, "wb") as file:
        pickle.dump(data, file)
        file.flush()
        fsync(file.fileno())
      
    rename(tmp_file, file_path) # Atomic instruction

def read_sequence_num_pub(file_path):
    seq_num = 0
    if exists(file_path):
        seq_num = pickle.load(open(file_path, "rb"))
    return seq_num

def read_sequence_num_sub(file_path):
    seq_num = 0
    last_get_id = {}
    if exists(file_path):
        [seq_num, last_get_id] = pickle.load(open(file_path, "rb"))
    return [seq_num, last_get_id]


def signal_handler(sig, frame):
    print('Pressing CTRL+C again may allow you to quit the program')
    sys.exit(1)

#!/usr/bin/env python3

about_ = '''
This is a simple script I put together to automate the process of mapping
the buttons on my wacom tablet. It takes at most one argument - a json file 
containing the key-mappings, along with the {name} and {type} of the wacom
device to which they should be mapped. 

If no arguments are supplied, the script will look for a file in a number
of pre-defined location (see below).

The script first checks to see if the desired mappings are already in use,
and then - only if there are discrepancies found - asks to proceed with the 
remapping operation.

{xsetwacom} must be installed for this script to work.
'''

# MODULES

import subprocess, json, re, shutil, argparse, pathlib, os

# VARIABLES

'''
A list of locations to look for a key-mapping file.
'''
default_map_locations_ = [
    pathlib.Path.home() / ".config/my-stuff/wacom-keymap.json",
    os.environ["MY_WACOM_KEYMAP"] if "MY_WACOM_KEYMAP" in os.environ else None,
    pathlib.Path(__file__).parent / "default.json",
]

# CONSTANTS

'''
Apply the following regular expression to lines of output from the 
command "xsetwacom --list devices" to generate the following capture 
groups: 0 = name, 1 = id, 2 = type
'''
device_matcher_ = re.compile(r'^(.+?)\s+id:\s+(\d+)\s+type:\s+(.*?)\s*$')
    
# FUNCTIONS

def get_device_id_(name_="Wacom Intuos Pro M Pad pad", type_="PAD"):
    '''
    Run the command "xsetwacom --list devices", then loop through the 
    output, looking for a line belonging to a device matching {name} and 
    {type}. Returns the device's {id} if a match is found, else {None}.
    '''
    _a = subprocess.run(
        ["xsetwacom", "--list", "devices"], 
        capture_output=True,
        text=True,
    )
    for _c in _a.stdout.splitlines():
        _d = device_matcher_.fullmatch(_c)
        if _d and _d.group(1) == name_ and _d.group(3) == type_:
            return _d.group(2)
    print(f'''Couldn't find device: {name_}, type: {type_}''')
    return None

def parse_mapping_file_(file_):
    '''
    Takes a key-mapping file in json format, checks to make sure it 
    contains the keys {name}, {type}, and {map}; then returns the
    mapping as a dictionary object. Otherwise returns {None}.
    '''
    try:
        with open(file_, "r") as _fp:
            _a = json.load(_fp)
    except:
        print(f'Failed to parse file: {file_}')
        return None
    for _b in "name", "type", "map":
        if _b not in _a:
            print("Map file is missing value: {_b}")
            return None
    return _a

def apply_map_(id_=None, map_=None):
    '''
    Loop through the button mappings contained in {map_}, and use 
    the command "xsetwacom set {id_} {args}" to apply each mapping 
    to the device whose id matches {id_}.
    '''
    for _a in map_:
        subprocess.run(["xsetwacom", "set", id_, _a[0], _a[1], _a[2]])

def check_map_(name_=None, type_=None, id_=None, map_=None):
    '''
    Prints a human-readable audit of which key-mappings in {map_}
    have been applied to the device matching {id_}. Returns {False} 
    if any mappings differ, or {True} if they are all the same.
    '''
    print(f'NAME: {name_}\nTYPE: {type_}')
    _m = True
    for _a in map_:
        _b = subprocess.run(
            ["xsetwacom", "get", id_, _a[0], _a[1]], 
            capture_output=True,
            text=True,
        )
        if _b.stdout.strip() == _a[2].strip():
            _c = f' YES | {_a[0]:<6} | {_a[1]:>2} | {_a[2]:<25}'
            if len(_a) >= 4:
                _c = f'{_c} | {_a[3]}'
            print(_c)
        else:
            print(f'> NO | {_a[0]} {_a[1]} = {_b.stdout} | SHOULD BE: {_a[2]}')
            _m = False
    if _m == False:
        print("MAPPING DID NOT MATCH!")
    else:
        print("ALL GOOD!")
    return _m

def configure_map_(name_=None, type_=None, id_=None, map_=None):
    '''
    Checks if key-mappings in {map_} are currently set for device 
    matching {id_}. Gives the user the option to apply the mappings 
    if they aren't applied already. Repeats until mappings match 
    or the user declines to continue trying.
    '''
    while True:
        _a = check_map_(id_=id_, map_=map_, name_=name_, type_=type_)
        if _a == True: 
            return True
        while True:
            _b = input("\nWould you like to apply this map? (y/n): ")
            if _b == "y":
                apply_map_(id_=id_, map_=map_, name_=name_, type_=type_)
                break
            if _b == "n":
                return False

def find_mapping_file_(map_location_list_):
    '''
    Loops through a list of strings and returns the first one that
    resolves to a valid file location.
    '''
    if type(map_location_list_) is str:
        map_location_list_ = [map_location_list_]
    for _a in map_location_list_:
        if not _a:
            continue
        _b = pathlib.Path(_a)
        if _b.is_file():
            return _b
    print(f'No mapping file.')
    return None

# SCRIPT

if not shutil.which("xsetwacom"):
    print("Couldn't find executable: xsetwacom")
    exit()

parser_ = argparse.ArgumentParser(
    prog = "My Shitty Wacom Keymapper",
    description = about_,
)
parser_.add_argument(
    "file_",
    nargs = "?",
    default = default_map_locations_,
    help = "The location of a file containing key-mappings."
)
args_ = parser_.parse_args()

file_ = find_mapping_file_(args_.file_)
if not file_:
    exit()

dict_ = parse_mapping_file_(file_)
if not dict_:
    exit()

id_ = get_device_id_(name_=dict_["name"], type_=dict_["type"])
if not id_:
    exit()

configure_map_(id_=id_, map_=dict_["map"], name_=dict_["name"], type_=dict_["type"])
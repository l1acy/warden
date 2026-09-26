import os

def get_config_folder_path():
    return os.path.expanduser('~/.config/warden')

def get_config_file(filename: str):
    return os.path.join(get_config_folder_path(), filename)
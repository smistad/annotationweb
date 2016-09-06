import os


def create_folder(path):
    try:
        os.mkdir(path)  # Make dataset path if doesn't exist
    except:
        pass
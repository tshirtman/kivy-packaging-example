from inspect import currentframe
from os.path import exists

from kivy.lang import Builder

def load_kv():
    filename = currentframe().f_back.f_code.co_filename
    if '_ft_' in filename:
        filename = filename.replace('_ft_', '')

    f = filename[:-2] + 'kv'
    if exists(f):
        return Builder.load_file(f)

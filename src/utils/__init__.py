from inspect import currentframe
from os.path import exists

from kivy.lang import Builder


def load_kv():
    '''
    This function allows keeping a separate kv file during development,
    for each module, while another tool can later replace all the calls
    with the inlined kv file in the source code.
    '''
    filename = currentframe().f_back.f_code.co_filename

    # if filename was ran through condiment/runpy, the name is mangled
    if '_ft_' in filename:
        filename = filename.replace('_ft_', '')

    f = filename[:-2] + 'kv'
    if exists(f):
        return Builder.load_file(f)

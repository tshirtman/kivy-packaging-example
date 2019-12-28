from setuptools import setup, Extension

from glob import glob
from os.path import basename, join, exists, isdir
from os import walk, unlink, write, getenv, chdir, dup2, dup, fdopen, close, mkdir
from sys import platform, stdout, exit
from tempfile import mkstemp, TemporaryFile
from shutil import move, rmtree

# from subprocess import call
# from shlex import split
# from contextlib import contextmanager

import sys
import io
import logging

from jinja2 import Template
from Cython.Build import cythonize
from Cython.Distutils import build_ext

from kivy.atlas import Atlas
from condiment import Parser

log = logging.getLogger(__name__)


DEV = getenv('WITH_DEV')
NAME = getenv('WITH_NAME', 'Application')

__version__ = '1.0'


def template_packages():
    chdir('..')
    templates = [
        'project.spec',
        'project.iss',
    ]
    for s in templates:
        with open('packaging/preprocess/{}'.format(s)) as f:
            t = Template(f.read())
            output = t.render({'NAME': NAME, 'VERSION': __version__})
            with open('packaging/{}'.format(s), 'w') as out:
                out.write(output)

    chdir('src')



def xrmtree(path):
    if exists(path):
        rmtree(path)


def condiment():
    """Hardcode condiment option in python files."""

    targets = [
        'main.py',
        'config_patch.py',
        'contact.py',
    ]
    for t in targets:
        if not exists(t):
            log.info("{} doesn't exist, skipping".format(t))
            continue

        source = '{}'.format(t)
        dest = '_{}'.format(t)
        move(source, dest)
        Parser(
            input=dest,
            output=source
        ).do()
        unlink(dest)


def make_atlas():
    """method basically copied/adapted from kivy.atlas __main__"""

    sources = [
        'src/data/*.png',
    ]
    filenames = [fname for fnames in sources for fname in glob(fnames)]

    options = {'use_path': False}
    if not isdir('data'):
        mkdir('data')

    outname = 'data/theme'
    size = 4096

    ret = Atlas.create(outname, filenames, size, **options)
    if not ret:
        log.error('Error while creating atlas!')
        exit(1)

    fn, meta = ret
    log.info('Atlas created at', fn)
    log.info('%d image%s been created' % (len(meta),
          's have' if len(meta) > 1 else ' has'))


def bundle_kv():
    '''Look through the source code, everywhere the load_kv() function
    is called, inject the content of the kv file in place. If the python
    code is then cythonize, it makes it that much harder to inspect and
    modify the packaged program.
    '''
    def get_kv_source(fn):
        kv = fn[:-2] + 'kv'
        with open(kv, encoding='utf8') as f:
            source = f.read()
            res = source.replace('\\', r'\\')
        unlink(kv)
        return res

    for root, dirnames, filenames in walk('.'):
        for f in filenames:
            fn = join(root, f)
            if not f.endswith('.py'):
                continue

            tmp = tmpname = None
            start = ''
            with open(fn, encoding='utf8') as source:
                for line in source:
                    if not line.endswith('load_kv()\n'):
                        if tmp is None:
                            start += line
                        else:
                            write(tmp, line.encode('utf8'))
                        continue

                    if tmp is None:
                        tmp, tmpname = mkstemp()
                        write(tmp, start.encode('utf8'))
                        start = ''

                    write(tmp, b'from kivy.lang.builder import Builder\n')
                    write(tmp, line.replace(
                        'load_kv()', '{__INLINE_KV__}').format(
                            __INLINE_KV__='Builder.load_string("""'
                        ).encode('utf8'))
                    write(tmp, get_kv_source(fn).encode('utf8'))
                    write(tmp, b'""")')

            if tmp:
                close(tmp)
                unlink(fn)
                move(tmpname, fn)
                log.info("replaced {}".format(fn))
            else:
                log.info("skipped {}".format(fn))


if __name__ == '__main__':

    chdir('src')
    condiment()
    bundle_kv()
    make_atlas()

    targets = [
        x for x in (
            (glob('*.py') + glob('*/*.py') if not DEV else []) +
            glob('*.pyx') + glob('*/*.pyx')
        )
        if not basename(x).startswith('_') and basename(x) != 'main.py'
    ]

    setup(ext_modules=cythonize(targets))

    if not DEV:
        for target in targets:
            unlink(target)

    template_packages()

    chdir('..')

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from glob import glob
from os.path import basename, join, exists
from sys import platform, stdout, exit
from tempfile import mkstemp, TemporaryFile
from os import walk, unlink, write, getenv, chdir, dup2, dup, fdopen, close
from shutil import move, rmtree
from kivy.atlas import Atlas
from condiment import Parser
from jinja2 import Template
from subprocess import call
from shlex import split
from contextlib import contextmanager
import sys
import io


DEV = getenv('WITH_DEV')
NAME = getenv('WITH_NAME', 'Application')


def template_packages():
    chdir('..')
    templates = [
        'project.spec',
        'project.iss',
    ]
    for s in templates:
        with open('packaging/preprocess/{}'.format(s)) as f:
            t = Template(f.read())
            output = t.render({'NAME': NAME, 'VERSION': version})
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
            print("{} doesn't exist, skipping".format(t))
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
        'src/data/menu/menu_*.png',
        'src/data/keys/*.png',
        'src/data/icons/*.png',
        'src/data/mone/*.png',
        'src/data/parts/*.png',
    ]
    filenames = [fname for fnames in sources for fname in glob(fnames)]

    options = {'use_path': False}
    outname = 'data/theme'
    size = 4096

    ret = Atlas.create(outname, filenames, size, **options)
    if not ret:
        print('Error while creating atlas!')
        exit(1)

    fn, meta = ret
    print('Atlas created at', fn)
    print('%d image%s been created' % (len(meta),
          's have' if len(meta) > 1 else ' has'))


def bundle_kv():
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
            if f.endswith('.py'):
                tmp, tmpname = mkstemp()
                with open(fn, encoding='utf8') as source:
                    found = False
                    for line in source:
                        if line.endswith('load_kv()\n'):
                            found = True
                            line = line.replace(
                                'load_kv()', '{__INLINE_KV__}')
                            write(
                                tmp,
                                b'from kivy.lang.builder import Builder\n')
                            write(
                                tmp,
                                line.format(
                                    __INLINE_KV__='Builder.load_string("""'
                                ).encode('utf8')
                            )
                            write(
                                tmp, get_kv_source(fn).encode('utf8')
                            )
                            write(tmp, b'""")')
                        else:
                            write(tmp, line.encode('utf8'))
                close(tmp)
                if found:
                    unlink(fn)
                    move(tmpname, fn)
                    print("replaced {}".format(fn))
                else:
                    unlink(tmpname)
                    print("skipped {}".format(fn))


if __name__ == '__main__':
    chdir('src')

    with open('../packaging/version.txt') as f:
        version = f.read().strip()

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

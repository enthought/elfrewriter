import contextlib
import shutil
import subprocess
import sys
import tempfile

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import os.path as op

from elftools.elf.elffile import ELFFile

from ..errors import ELFRewriterError
from ..rewriter import ELFRewriter, _get_rpath_entry, _get_runpath_entry

DATA_DIR = op.join(op.dirname(__file__), "data")

MAIN_ABS_RPATH = op.join(DATA_DIR, "main_abs_rpath")

FILES_TO_RPATHS = {
    MAIN_ABS_RPATH: ["/yomama"],
}

FILES_TO_RPATHS_STRING = {
    MAIN_ABS_RPATH: "/yomama",
}

FILES_TO_DEPENDENCIES = {
    MAIN_ABS_RPATH: ["libc.so.6"],

}

def _ensure_has_patchelf():
    try:
        res = subprocess.call(["patchelf", "--version"], stdout=subprocess.PIPE)
        return res == 0
    except OSError:
        return False

HAS_PATCHELF = _ensure_has_patchelf()

@contextlib.contextmanager
def mkdtemp():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


class TestELFRewriter(unittest.TestCase):
    def test_invalid_file(self):
        """
        Ensure we bail with the right exception when opening a non-ELF
        file.
        """
        self.assertRaises(ELFRewriterError, lambda: ELFRewriter(__file__))

    def test_rpaths(self):
        for f, r_rpaths in FILES_TO_RPATHS.items():
            rewriter = ELFRewriter(f)
            self.assertEqual(rewriter.rpaths, r_rpaths)

    def test_rpaths_string(self):
        for f, r_rpath_string in FILES_TO_RPATHS_STRING.items():
            rewriter = ELFRewriter(f)
            self.assertEqual(rewriter.rpaths_string, r_rpath_string)

    def test_dependencies(self):
        for f, r_dependencies in FILES_TO_DEPENDENCIES.items():
            rewriter = ELFRewriter(f)
            self.assertEqual(rewriter.dependencies, r_dependencies)

    @unittest.skipIf(not HAS_PATCHELF, "Cannot run rpath writing tests without patchelf")
    def test_strip_rpath(self):
        with mkdtemp() as d:
            copy = op.join(d, op.basename(MAIN_ABS_RPATH))
            shutil.copy(MAIN_ABS_RPATH, copy)

            with ELFRewriter(copy) as rewriter:
                rewriter.rpaths = []

            rewriter = ELFRewriter(copy)
            self.assertEqual(rewriter.rpaths, [])
            self.assertEqual(rewriter.rpaths_string, "")

    @unittest.skipIf(not HAS_PATCHELF, "Cannot run rpath writing tests without patchelf")
    def test_change_rpath(self):
        with mkdtemp() as d:
            copy = op.join(d, op.basename(MAIN_ABS_RPATH))
            shutil.copy(MAIN_ABS_RPATH, copy)

            rewriter = ELFRewriter(copy)
            rewriter.rpaths.insert(0, "floupiga")
            rewriter.commit()

            rewriter = ELFRewriter(copy)
            self.assertEqual(rewriter.rpaths, ["floupiga"] + FILES_TO_RPATHS[MAIN_ABS_RPATH])
            self.assertEqual(rewriter.rpaths_string, "floupiga:/yomama")

            with open(copy, "rb") as fp:
                elf_handle = ELFFile(fp)
                self.assertEqual(_get_rpath_entry(elf_handle), None)
                self.assertEqual(_get_runpath_entry(elf_handle), "floupiga:/yomama")

    @unittest.skipIf(not HAS_PATCHELF, "Cannot run rpath writing tests without patchelf")
    def test_change_rpath_force_dt_rpath(self):
        with mkdtemp() as d:
            copy = op.join(d, op.basename(MAIN_ABS_RPATH))
            shutil.copy(MAIN_ABS_RPATH, copy)

            rewriter = ELFRewriter(copy, force_dt_rpath=True)
            rewriter.rpaths.insert(0, "floupiga")
            rewriter.commit()

            rewriter = ELFRewriter(copy)
            self.assertEqual(rewriter.rpaths, ["floupiga"] + FILES_TO_RPATHS[MAIN_ABS_RPATH])
            self.assertEqual(rewriter.rpaths_string, "floupiga:/yomama")

            with open(copy, "rb") as fp:
                elf_handle = ELFFile(fp)
                self.assertEqual(_get_rpath_entry(elf_handle), "floupiga:/yomama")

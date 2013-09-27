import unittest

import os.path as op

from ..errors import ELFRewriterError
from ..rewriter import ELFRewriter

DATA_DIR = op.join(op.dirname(__file__), "data")

MAIN_ABS_RPATH = op.join(DATA_DIR, "main_abs_rpath")

FILES_TO_RPATHS = {
    MAIN_ABS_RPATH: ["/yomama"],
}

FILES_TO_DEPENDENCIES = {
    MAIN_ABS_RPATH: ["libc.so.6"],

}

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

    def test_dependencies(self):
        for f, r_dependencies in FILES_TO_DEPENDENCIES.items():
            rewriter = ELFRewriter(f)
            self.assertEqual(rewriter.dependencies, r_dependencies)

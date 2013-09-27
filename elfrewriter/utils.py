from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError

def is_elf(path):
    with open(path, "rb") as fp:
        try:
            ELFFile(fp)
            return True
        except ELFError:
            return False


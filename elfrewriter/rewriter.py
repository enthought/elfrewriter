from elftools.common.py3compat import bytes2str
from elftools.elf.elffile import ELFFile
from elftools.elf.dynamic import DynamicSection

from .errors import ELFRewriterError
from .utils import is_elf

PATHSEP = ":"

def _get_rpath_entry(elf_handle):
    for section in elf_handle.iter_sections():
        if not isinstance(section, DynamicSection):
            continue

        for tag in section.iter_tags():
            # XXX: is there only one RD_RPATH entry ?
            if tag.entry.d_tag == 'DT_RPATH':
                return bytes2str(tag.rpath)

def _get_dependencies(elf_handle):
    shared_libraries = []
    
    for section in elf_handle.iter_sections():
        if isinstance(section, DynamicSection):
            for tag in section.iter_tags():
                if tag.entry.d_tag == 'DT_NEEDED':
                    shared_libraries.append(bytes2str(tag.needed))

    return shared_libraries

class ELFRewriter(object):
    """
    ELFRewriter can be used to query and change elf properties relevant for
    relocatability.

    Concretely, you can query/modify the following:

        - rpaths sections
        - dependencies
    """
    def __init__(self, filename):
        self.filename = filename

        if not is_elf(filename):
            raise ELFRewriterError("File %s is not an ELF file." % (filename,))

        with open(filename, "rb") as fp:
            self._elf_handle = ELFFile(fp)
            rpath = _get_rpath_entry(self._elf_handle)
            self._rpaths = rpath.split(PATHSEP)
            self._dependencies = _get_dependencies(self._elf_handle)

    @property
    def rpaths(self):
        """
        The list of rpaths.
        """
        return self._rpaths

    @property
    def dependencies(self):
        """
        The list of dependencies.

        Note
        ----
        This differs from the ldd output:

            - we don't list the linux-vdo.so 'library' (which is virtual
              http://blogs.igalia.com/aperez/2009/01/13/the-story-of-linux-gatevdsoso/).
            - we don't list the ELF interpreter either (e.g.
              ld-linux_x86-64.so)
        """
        return self._dependencies

import subprocess

from elftools.common.py3compat import bytes2str
from elftools.elf.elffile import ELFFile
from elftools.elf.dynamic import DynamicSection

from .errors import ELFRewriterError
from .utils import is_elf

PATHSEP = ":"

def _get_rpath_entry(elf_handle):
    """
    Returns the value of the DT_RPATH entry in the ELF header, or None if not
    set.
    """
    for section in elf_handle.iter_sections():
        if not isinstance(section, DynamicSection):
            continue

        for tag in section.iter_tags():
            # XXX: is there only one RD_RPATH entry ?
            if tag.entry.d_tag == 'DT_RPATH':
                return bytes2str(tag.rpath)

def _get_runpath_entry(elf_handle):
    """
    Returns the value of the DT_RUNPATH entry in the ELF header, or None if not
    set.
    """
    for section in elf_handle.iter_sections():
        if not isinstance(section, DynamicSection):
            continue

        for tag in section.iter_tags():
            # XXX: is there only one RD_RUNPATH entry ?
            if tag.entry.d_tag == 'DT_RUNPATH':
                return bytes2str(tag.runpath)

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

    Parameters
    ----------
    filename: str
        The path to the ELF file
    force_dt_rpath: bool
        When modifying the elf file, the new rpath entry is written to
        DT_RUNPATH. If force_dt_rpath is set to True, both DT_RUNPATH and
        DT_RPATH are written (to the same value).

    Note
    ----
    ELF has two ways of defining rpath: DT_RPATH or DT_RUNPATH. DT_RUNPATH is
    strictly better than DT_RPATH, but newer.

    If *both* DT_RPATH and DT_RUNPATH as set, only DT_RUNPATH is considered
    (same rule as the ELF-loader). IOW:

        - if only DT_RPATH is set, ELFRewriter.rpaths corresponds to DT_RPATH
        - if only DT_RUNPATH is set, ELFRewriter.rpaths corresponds to DT_RUNPATH
        - if both are defined, DT_RPATH is ignored, and ELFRewriter.rpaths
          corresponds to DT_RUNPATH.
    """
    def __init__(self, filename, force_dt_rpath=False):
        self.filename = filename
        self._force_dt_rpath = force_dt_rpath

        if not is_elf(filename):
            raise ELFRewriterError("File %s is not an ELF file." % (filename,))

        with open(filename, "rb") as fp:
            self._elf_handle = ELFFile(fp)
            rpath = _get_rpath_entry(self._elf_handle)
            runpath = _get_runpath_entry(self._elf_handle)
            if runpath is None:
                if rpath is None or len(rpath) == 0:
                    self.rpaths = []
                else:
                    self.rpaths = rpath.split(PATHSEP)
            else:
                if runpath is None or len(runpath) == 0:
                    self.rpaths = []
                else:
                    self.rpaths = runpath.split(PATHSEP)
            self._dependencies = _get_dependencies(self._elf_handle)

    def commit(self):
        try:
            if self._force_dt_rpath:
                cmd = ["patchelf", "--force-rpath", "--set-rpath",
                       self.rpaths_string, self.filename]
            else:
                cmd = ["patchelf", "--set-rpath", self.rpaths_string,
                       self.filename]
            subprocess.check_call(cmd)
        except OSError:
            raise ELFRewriterError("Could not write changes back to {0}".format(self.filename))

    @property
    def rpaths_string(self):
        return PATHSEP.join(self.rpaths)

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

Elfrewriter is a small set of tools built on top of pyelftools to retrieve and
change informations about elf binaries. It is mostly concerned with ELF
features relevant to make relocatable binaries (DT_RUNPATH feature).

Example::

        from elfrewriter import ELFRewriter

        rewriter = ELFRewriter("a.out")
        print rewriter.dependencies
        print rewriter.rpaths

        # One can change rpaths, but changes will only be written after commit
        # has been called (see also known limitations).
        rewriter = ELFRewriter("a.out")
        rewriter.rpaths = ["yo", "mama"]
        rewriter.commit()

        # Use a context manager to ensure changes are committed
        with ELFRewriter("a.out") as rewriter:
            rewriter.rpaths = ["yo", "mama"]

Main features:

        - ability to query/change rpath
        - ability to query/change the dependencies

Known limitations:

        - modification is done through patchelf binary in a subprocess:
          http://nixos.org/patchelf.html. In theory, one could implement the
          feature using pyelftools, but that would be quite a bit of work in
          the case where the rpath entry needs to grow. Patches welcome though !
        - consequence of the above: while querying works on any platform
          supported by pyelftools, modifying a binary only works on a machine
          with patchelf (most likely only Linux).

Development happens on `github <http://github.com/enthought/elfrewriter>`_

# PyPulsar — historical solid-state NMR simulator

PyPulsar is the graphical, Python-scriptable version of the PULSAR solid-state
NMR simulation program by Jean-Paul Amoureux and Christian Fernandez.
It was previously hosted on **[SourceForge](https://sourceforge.net/projects/pypulsar/)**.

This repository preserves earlier work as a traceable scientific reference
for [SpectroChemPy](https://github.com/spectrochempy/spectrochempy) and its
[NMR plugin](https://github.com/spectrochempy/spectrochempy_nmr).

## Preserved version

The imported archive is **SourceForge SVN revision 385, `trunk`**.
The archive contains differing version metadata, all preserved:

- `pypulsar/version.py`: `0.2.alpha1.-46-337` (10 June 2008);
- `pypulsar/build/version.py`: `0.2.alpha1.0-383` (24 July 2008);
- top-level `version.py`: project `0.2`, revision `197` (8 May 2007).

The unambiguous identifier for this import is the SVN **r385 trunk snapshot**.
The original [development warning](WARNING.txt) remains part of the snapshot.

- [`sourceforge-r385`](https://github.com/fernandezc/pypulsar/tree/sourceforge-r385)
  identifies the original 238-file source tree, before repository documentation
  and the additional license grant were added.
- [PROVENANCE.md](PROVENANCE.md) records the archive checksum, import procedure,
  and links to the original project and SVN repository.
- [The original downloaded ZIP](provenance/pypulsar-code-r385-trunk.zip) and a
  [per-file SHA-256 manifest](provenance/sourceforge-r385.json) are included.

This is a snapshot import; the original SVN revision history remains on
SourceForge. It is not presented as a reconstruction of that history.

## What is here

- [Fortran simulation engine](pulsar/).
- [Historical Python simulation API](pypulsar/functions.py).
- [Graphical application and script editor](pypulsar/).
- [Sequence examples](pypulsar/workspace/models/), including Hahn echo,
  real pulses, MQMAS coherence selection and cross-polarization.
- [Original application introduction and scientific reference](pypulsar/README.html).

Scripts use `Simulation`, `Nucleus`, `set_pulse`, `set_delay`, phase/offset
settings, coherence selection and Python loops. Historical time values are
in **microseconds** (`usec = 1`); the current SpectroChemPy NMR API uses seconds.

The original application targets Python 2 and its contemporary wxPython,
NumPy/SciPy and Fortran toolchain. Preservation checks do not establish that
the historical GUI or numerical engine runs on a modern installation.

## Licensing

With authorization from Christian Fernandez, the project-owned code is
additionally available under **CeCILL-B**, the license used by SpectroChemPy.
The precise file scope and retained third-party exceptions are documented in
[LICENSING.md](LICENSING.md). Original author credits and GPL notices are
preserved verbatim as part of the historical record. Third-party components
retain their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Verify the reference

With Python 3, run:

```sh
python3 tools/verify_snapshot.py
```

This checks the original archive checksum and all 238 imported files against
the archive and manifest, without importing or running historical PyPulsar.

For the earlier published 0.1 series, see the original
[SourceForge tags](https://svn.code.sf.net/p/pypulsar/code/tags/), including
[pyPulsar-0.1.186](https://svn.code.sf.net/p/pypulsar/code/tags/pyPulsar-0.1.186/).

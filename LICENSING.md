# Licensing and historical notices

## Additional CeCILL-B grant — 18 November 2026

Christian Fernandez, as rights holder for the PyPulsar project code, has
authorized this GitHub publication and an additional **CeCILL-B** license
grant for the project-owned source listed below. The full license is in
[LICENSE](LICENSE), matching the license used by SpectroChemPy.

The additional grant applies to the project-owned implementation in:

- `pulsar/*.f90` and `pulsar/compiler.bat`;
- `pypulsar/*.py`, **except** `enhancedstatusbar.py` and `figcanvas.py`;
- `pypulsar/build/*.py`;
- `pypulsar/workspace/models/*.tpl`;
- the top-level `version.py`;
- the new repository documentation and `tools/verify_snapshot.py`.

Original attribution to Jean-Paul Amoureux and Christian Fernandez is retained.
The project-owned files above may be used under this additional CeCILL-B grant
even where their unchanged historical headers describe the earlier GPL terms.

## Original distribution

The original SourceForge distribution contains GNU GPL version 2-or-later
notices, including in Python and Fortran source headers. Its bundled license
text remains in [pypulsar/build/COPYING.rtf](pypulsar/build/COPYING.rtf).
Those bytes, author credits and historical documentation have not been rewritten.
The pristine `sourceforge-r385` tag predates the additional grant recorded here.

## Scope exclusions

This grant does not relicense third-party code or fragments, third-party
artwork, or the text of any pre-existing license. In particular:

- `pypulsar/enhancedstatusbar.py` retains its wxPython license notice;
- `python/Python25/numpy/distutils/fcompiler/intel.py` is historical NumPy code
  and is outside the additional grant;
- `pypulsar/figcanvas.py` contains an attributed external recipe adaptation;
  the entire file is excluded from the additional grant and retains its
  historical notices;
- historical images/resources and other material outside the explicit source
  list above retain their original distribution terms and attribution.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This is a scoped additional
grant for the project-owned implementation, not a claim that all contents of
the old archive have one uniform license.

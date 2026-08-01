# Contributing to pyALDIC-3D

Thanks for being here. pyALDIC-3D is young software meeting real-world rigs for
the first time, so a report of *"it broke on my data"* is worth as much as a
patch.

## Ways to help, easiest first

1. **Tell us it broke.** [Open an issue](https://github.com/zachtong/pyALDIC-3D/issues/new/choose)
   with the version (`al-dic-3d --version`), your OS, and the LOG panel's saved
   output (**LOG → Save…**). A small shareable dataset that reproduces the
   problem is the fastest path to a fix.
2. **Ask or answer in [Discussions](https://github.com/zachtong/pyALDIC-3D/discussions).**
   Usage questions belong there rather than in Issues. English and 中文 are both
   welcome — please tag Chinese posts with `[中文]` in the title.
3. **Improve the docs.** The user guide lives in `docs/user-guide/`. Typos,
   unclear steps and missing screenshots are all fair game.
4. **Send code.** See below.

## Development setup

```bash
git clone https://github.com/zachtong/pyALDIC-3D.git
cd pyALDIC-3D
pip install -e ".[dev]"      # app + pytest, ruff, pre-commit, matplotlib
pre-commit install           # optional but recommended
pytest                       # the full suite should be green before you start
```

The 2D correlation engine (`al-dic`) is consumed as a **pinned, read-only
library**. If you want to develop against a local checkout of it, install the
sibling repo editable first — it satisfies the same version pin:

```bash
pip install -e ../pyALDIC
```

Never modify the 2D repo from a 3D change. If a fix genuinely belongs there,
say so in the issue and it will be done in a separate 2D pull request.
`docs/DEPENDS_ON_2D.md` is the ledger of exactly which `al_dic` symbols this
project uses — add a row if your change imports a new one.

## House rules

- **Tests first.** New behaviour arrives with a test that fails before the fix
  and passes after it. Aim for 80%+ coverage on new modules.
- **Keep the compute layer Qt-free.** `calibration`, `sequence`, `matching`,
  `reconstruct`, `strain3d` and `export` must import cleanly on a headless
  server; only `viz3d`, `gui` and `i18n` may touch Qt or OpenGL. There is an
  architecture test that enforces this.
- **Files stay under 800 lines**, functions small, dataclasses frozen. `NaN`
  means invalid and must propagate rather than being filled in.
- **Every user-facing string goes through `self.tr()`** and lands in all eight
  locales (`python tools/i18n.py extract` then `compile`). The pseudo-locale
  scan (`python tools/i18n.py scan`) must stay clean.
- **Lint before pushing:** `ruff check . && ruff format .`.
- **Conventional commits** (`feat:`, `fix:`, `docs:`, `perf:`, `test:`,
  `refactor:`, `chore:`, `ci:`), one logical change per commit.

## Pull requests

1. Branch off `main`.
2. Make the change, with tests.
3. Run `pytest` and `ruff check .` locally — CI runs the full suite on
   Windows, macOS and Linux against Python 3.10 and 3.12.
4. Describe *what* changed and *why*, and say how you verified it. If the
   change touches the correlation, reconstruction or strain path, mention
   whether the MATLAB-parity gates still pass.

## Figures and marketing assets

The README figures are all generated: every image under `assets/` has a script
under `tools/marketing/` that reproduces it headlessly from the shipping code.
If you change something a figure illustrates, re-run the matching generator
rather than editing the PNG.

## Licence

By contributing you agree that your contribution is licensed under the
project's [BSD 3-Clause](LICENSE) licence.

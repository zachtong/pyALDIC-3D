# Releasing pyALDIC-3D

The maintainer's runbook for publishing `al-dic-3d` to PyPI, shipping the
Windows installer, and minting Zenodo DOIs. Written for the **first public
release (v1.0.0)** and every release after it. Nothing in this document runs
automatically — it is the human ceremony that the prepared artifacts
(`publish.yml`, `build-exe.yml`, `CHANGELOG.md`, `CITATION.cff`, `.zenodo.json`)
wait for.

Every release ships three things from one tag: the wheel + sdist on PyPI, the
Windows installer `pyALDIC-3D-X.Y.Z-win64-setup.exe` on the GitHub Release, and
the Zenodo archive. The installer is not optional: 1.0.1 and 1.0.2 went out
without one because this runbook never mentioned it.

> **Versioning note.** The package version has exactly one source of truth:
> `__version__` in `src/al_dic_3d/__init__.py` (pyproject reads it via
> hatchling's dynamic-version hook). Git tags are `v<__version__>` and
> `publish.yml` refuses to publish when they disagree. The "v1.x" entries in
> `docs/architecture/00_INDEX.md` are **internal documentation milestones** —
> they are NOT package versions and are never tagged or published. Do not try
> to reconcile the two numbering schemes; only `__version__` matters here.

---

## A. One-time setup (before the first release)

Done for v1.0.0; kept for the record and for a re-setup. Do these three steps
**in order** — the PyPI pending publisher and the Zenodo switch both need the
repo, and Zenodo needs it public.

### A.1 Flip the GitHub repo public

1. Open <https://github.com/zachtong/pyALDIC-3D/settings>.
2. Scroll to the **Danger Zone** → **Change repository visibility** →
   **Change visibility** → **Make public**.
3. Type the repository name to confirm.

Pre-flip checklist (all prepared already, verify once):

- [ ] `LICENSE` present (BSD-3-Clause) and matches `pyproject.toml`
      `license = "BSD-3-Clause"`.
- [ ] No secrets in history (`.claude/settings.json` and CLAUDE.md are
      intentionally versioned and contain none).
- [ ] `reports/`, `reference/`, `.venv/`, `*.aldic3d` are gitignored.

### A.2 Register the PyPI *pending* Trusted Publisher

Trusted Publishing lets GitHub Actions publish with a short-lived OIDC
identity — **no API token is ever created or stored**. Because `al-dic-3d`
does not exist on PyPI yet, register a *pending* publisher (it claims the
project name and converts to a normal publisher on first upload):

1. Log in to <https://pypi.org> (the account that owns `al-dic`).
2. Click your avatar (top right) → **Your account** → in the left sidebar
   choose **Publishing** (direct URL: <https://pypi.org/manage/account/publishing/>).
3. Under **"Add a new pending publisher"**, select the **GitHub** tab and fill
   in exactly:

   | Field | Value |
   |---|---|
   | PyPI project name | `al-dic-3d` |
   | Owner | `zachtong` |
   | Repository name | `pyALDIC-3D` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

4. Click **Add**.

Then create the matching GitHub Actions environment (the workflow's
`environment: pypi` gate):

1. <https://github.com/zachtong/pyALDIC-3D/settings/environments> →
   **New environment** → name it exactly `pypi` → **Configure environment**.
2. (Optional but recommended) add yourself under **Required reviewers** so a
   publish waits for one manual approval click.

### A.3 Enable the GitHub–Zenodo integration (requires public repo)

1. Log in to <https://zenodo.org> **with the GitHub log-in option** (or link
   GitHub under Account → Linked accounts) using the account that should own
   the record.
2. Click your username (top right) → **GitHub** (direct URL:
   <https://zenodo.org/account/settings/github/>).
3. If `zachtong/pyALDIC-3D` is not listed, click **Sync now** (top right of
   that page) — it appears only once the repo is public.
4. Flip the toggle next to **`zachtong/pyALDIC-3D`** to **ON**.

From now on Zenodo archives **every published GitHub Release** and mints:

- a **version DOI** for that release, and
- (on the first release) a **concept DOI** that always resolves to the latest
  version — this is the DOI to put in `README.md` and `CITATION.cff`.

Zenodo reads the record metadata (title, creators, license, keywords, related
identifiers) from the versioned **`.zenodo.json`** at the repo root.

> **Important:** Zenodo is triggered by publishing a **GitHub Release**, not by
> pushing a tag. A bare `git push origin v1.0.0` never reaches Zenodo. Our
> `publish.yml` creates the Release automatically after a successful PyPI
> publish (or reuses one you created manually), so the trigger is guaranteed —
> but only *after* the A.3 toggle is ON.

---

## B. Per-release ceremony

For every release `vX.Y.Z`:

1. **Bump the version everywhere it is written down.** `__version__` is the
   only value the build reads, but the copies below are what users and
   citation managers see, and they drift silently (`CITATION.cff` still carried
   the 1.0.0 release date at 1.1.0):

   | File | What to change |
   |---|---|
   | `src/al_dic_3d/__init__.py` | `__version__ = "X.Y.Z"` — the single source of truth (pyproject, both workflows and the installer build read it) |
   | `CITATION.cff` | `version: X.Y.Z` **and** `date-released: "YYYY-MM-DD"` — the day the GitHub Release is published |
   | `docs/user-guide/index.md` | "It documents pyALDIC-3D **X.Y.x**" |
   | `docs/user-guide/02-installation-launching.md` | the sample output of `al-dic-3d --version` |
   | `README.md` | the *Latest release* cell of the comparison table, the installer file name under *Installation*, and `version = {X.Y.Z}` in the BibTeX block |

   Then look for leftovers: `git grep -n "<previous version>"`.

2. **CHANGELOG.md** — rename `## [Unreleased]` to `## [X.Y.Z] — YYYY-MM-DD`,
   delete the subsections it left empty and any `<!-- ... -->` placeholders,
   put a fresh empty `## [Unreleased]` above it, and update the link
   references at the bottom (`[Unreleased]: .../compare/vX.Y.Z...HEAD` and a
   new `[X.Y.Z]: .../compare/v<previous>...vX.Y.Z`). **This section becomes the
   GitHub release notes** — `publish.yml` extracts it verbatim — so write it
   for users. Preview exactly what they will read:

   ```bash
   python packaging/extract_changelog.py X.Y.Z
   ```

   Also record the release in `docs/architecture/00_INDEX.md`'s changelog
   (the internal milestone log; keep the package version labelled as such).

3. **Verify locally** (green before tagging):

   ```bash
   ruff check . && pytest -q -m "not perf"
   python -m build && python -m twine check dist/*
   ```

   If the release touches packaging or `packaging/requirements-build.txt`,
   also build the installer before tagging: run
   `packaging\build_installer.ps1` locally, or dispatch **Build Windows
   Installer** (`build-exe.yml`) on `main` with no tag. Both end with the
   frozen self-test.

4. **Commit and tag** (conventional commit, single author, no trailers):

   ```bash
   git commit -am "chore(release): vX.Y.Z"
   git tag -a vX.Y.Z -m "pyALDIC-3D vX.Y.Z"
   git push origin main vX.Y.Z
   ```

5. **CI publishes** — the tag push starts two workflows:

   - `.github/workflows/publish.yml`: build → `twine check` →
     tag-vs-`__version__` guard → PyPI Trusted Publishing (environment
     `pypi`; approve it if you enabled required reviewers) → creates the
     **GitHub Release** for the tag, with the `CHANGELOG.md` section as its
     notes, and attaches the sdist + wheel.
   - `.github/workflows/build-exe.yml`: the same tag guard →
     `packaging/build_installer.ps1` on `windows-latest` (clean venv from the
     pinned `requirements-build.txt` → PyInstaller → frozen
     `pyaldic3d-cli.exe self-test` → Inno Setup) → silent install / run /
     uninstall of the installer → attaches
     `pyALDIC-3D-X.Y.Z-win64-setup.exe` and its `.sha256` to the Release once
     `publish.yml` has created it (it waits up to 30 minutes). An installer
     failure never blocks the PyPI release.

   *Re-run safety:* the publish step uses `skip-existing: true`, the Release
   step reuses an existing Release (`--clobber` for artifacts), and the
   installer attach uses `--clobber`, so re-running a partially failed
   workflow is safe and idempotent.

6. **Verify the Release** — its page must show your `CHANGELOG.md` section
   and four assets: the wheel, the sdist, the installer and its `.sha256`
   (plus GitHub's own source archives). Then check the PyPI install in a clean
   environment:

   ```bash
   python -m venv /tmp/relcheck && . /tmp/relcheck/bin/activate   # or conda
   pip install "al-dic-3d==X.Y.Z"
   al-dic-3d --version    # must print X.Y.Z
   al-dic-3d --help
   ```

   and, on a Windows desktop, install the downloaded installer once and open
   the GUI (CI cannot open a real window with OpenGL).

7. **Zenodo mints the DOI** — the GitHub Release publication (step 5) triggers
   Zenodo automatically. Check <https://zenodo.org/account/settings/github/>:
   the repo row shows the new record within a few minutes. Open the record and
   note **both** DOIs (version DOI + concept DOI).

8. **First release only (done for v1.0.0) — paste the concept DOI back** into:
   - `README.md` → Citation section (replace the "pending first release"
     wording, add the DOI badge if desired);
   - `CITATION.cff` → uncomment the `identifiers:` block and fill in the
     concept DOI, set `date-released`;
   - commit as `docs: add Zenodo concept DOI` (no new tag needed — the DOI
     text lands in the next release's archive, which is normal practice).

---

## C. Troubleshooting

- **PyPI upload rejected: "invalid-publisher"** — the pending-publisher
  fields must match *exactly* (workflow filename `publish.yml`, environment
  `pypi`, owner/repo case-insensitive). Fix on
  <https://pypi.org/manage/account/publishing/> and re-run the workflow
  (`Actions → Publish to PyPI → Re-run` or a manual `workflow_dispatch`).
- **Tag/version mismatch** — the build job fails with an explicit error; fix
  `__version__`, commit, delete and re-create the tag
  (`git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`, then re-tag).
- **Zenodo record missing** — verify the A.3 toggle is ON *before* the Release
  is published; a Release published earlier is not archived retroactively.
  Simplest fix: toggle ON, then publish a new patch release.
- **`workflow_dispatch` run of `publish.yml`** — builds and (thanks to
  `skip-existing`) no-op-publishes; the Release step is skipped because there
  is no tag ref. Use it to smoke-test the trusted-publisher wiring without a
  version bump.
- **The installer is missing from the Release** — open the *Build Windows
  Installer* run for the tag. If the build failed, fix it and re-run. If only
  the attach job failed because the Release did not appear within 30 minutes
  (for example `publish.yml` was waiting for the `pypi` approval), re-run
  *Build Windows Installer* via `workflow_dispatch` with `tag=vX.Y.Z` once the
  Release exists.
- **The frozen self-test failed** — the failing checks are printed in the
  *Build* step; the complete log is the run's `build-log` artifact.
  Reproduce locally with `packaging\build_installer.ps1`.
- **The release notes are only a "Full Changelog" link** — `CHANGELOG.md` had
  no `## [X.Y.Z]` section at the tag, so the Release fell back to generated
  notes. An existing Release's notes are never rewritten by a re-run; set them
  by hand:

  ```bash
  python packaging/extract_changelog.py X.Y.Z -o notes.md
  gh release edit vX.Y.Z --notes-file notes.md
  ```

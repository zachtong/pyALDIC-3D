# Releasing pyALDIC-3D

The maintainer's runbook for publishing `al-dic-3d` to PyPI and minting Zenodo
DOIs. Written for the **first public release (v1.0.0)** and every release after
it. Nothing in this document runs automatically — it is the human ceremony that
the prepared artifacts (`publish.yml`, `CITATION.cff`, `.zenodo.json`) wait for.

> **Versioning note.** The package version has exactly one source of truth:
> `__version__` in `src/al_dic_3d/__init__.py` (pyproject reads it via
> hatchling's dynamic-version hook). Git tags are `v<__version__>` and
> `publish.yml` refuses to publish when they disagree. The "v1.x" entries in
> `docs/architecture/00_INDEX.md` are **internal documentation milestones** —
> they are NOT package versions and are never tagged or published. Do not try
> to reconcile the two numbering schemes; only `__version__` matters here.

---

## A. One-time setup (before the first release)

Do these three steps **in order** — the PyPI pending publisher and the Zenodo
switch both need the repo, and Zenodo needs it public.

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

For every release `vX.Y.Z` (including the first, `v1.0.0`):

1. **Bump the version** — edit `src/al_dic_3d/__init__.py`:

   ```python
   __version__ = "X.Y.Z"
   ```

   and update `version:` in `CITATION.cff` to match.

2. **Changelog** — record the release in `docs/architecture/00_INDEX.md`'s
   changelog (internal doc milestones live there too; keep the package version
   clearly labelled as such).

3. **Verify locally** (green before tagging):

   ```bash
   ruff check . && pytest -q
   python -m build && python -m twine check dist/*
   ```

4. **Commit and tag** (conventional commit, single author, no trailers):

   ```bash
   git commit -am "chore(release): vX.Y.Z"
   git tag -a vX.Y.Z -m "pyALDIC-3D vX.Y.Z"
   git push origin main vX.Y.Z
   ```

5. **CI publishes** — the tag push triggers `.github/workflows/publish.yml`:
   build → `twine check` → tag-vs-`__version__` guard → PyPI Trusted
   Publishing (environment `pypi`; approve it if you enabled required
   reviewers) → creates/updates the **GitHub Release** for the tag with the
   sdist + wheel attached.

   *Re-run safety:* the publish step uses `skip-existing: true` and the
   Release step reuses an existing Release (`--clobber` for artifacts), so
   re-running a partially failed workflow — or a `workflow_dispatch` dry run —
   is safe and idempotent.

6. **Verify the PyPI install** in a clean environment:

   ```bash
   python -m venv /tmp/relcheck && . /tmp/relcheck/bin/activate   # or conda
   pip install "al-dic-3d[gui,viz3d]==X.Y.Z"
   al-dic-3d --version    # must print X.Y.Z
   al-dic-3d --help
   ```

7. **Zenodo mints the DOI** — the GitHub Release publication (step 5) triggers
   Zenodo automatically. Check <https://zenodo.org/account/settings/github/>:
   the repo row shows the new record within a few minutes. Open the record and
   note **both** DOIs (version DOI + concept DOI).

8. **First release only — paste the concept DOI back** into:
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
- **`workflow_dispatch` run** — builds and (thanks to `skip-existing`)
  no-op-publishes; the Release step is skipped because there is no tag ref.
  Use it to smoke-test the trusted-publisher wiring without a version bump.

# 3. Loading stereo images

Stereo-DIC needs **two synchronized image sequences** — one per camera. The
**IMAGES** panel at the top of the left sidebar has two drop zones, LEFT and
RIGHT, side by side.

## The LEFT / RIGHT drop zones

Each drop zone reads *Drop LEFT camera folder or click* (and *Drop RIGHT camera
folder or click*). To load a camera's frames:

- **Click** the zone to open a folder picker (*Select image folder*), or
- **Drag a folder** onto the zone. Dropping any *file* that lives in a folder
  also works — the zone uses that file's parent folder.

Once loaded, the zone shows the folder name and the frame count (e.g.
`my_left\n34 frames`) with an accent border; hovering shows the full path.

Recognized image extensions are `.png`, `.tif`, `.tiff`, `.jpg`, `.jpeg`, and
`.bmp`.

## Both cameras in one folder

Many rigs write both cameras into the same folder. When every image in a
dropped folder follows one of these naming schemes, each zone takes only its
own camera's images, so the same folder can be dropped on both zones:

| Left camera | Right camera |
|---|---|
| `L_0001.tif`, `L0001.tif` | `R_0001.tif`, `R0001.tif` |
| `left_01.png` | `right_01.png` |
| `img_cam0_001.png` | `img_cam1_001.png` (also `cam1` / `cam2`) |
| `0000_0.tif` (DICe) | `0000_1.tif` |
| `specimen_L.png` | `specimen_R.png` |

The log names the scheme it recognised. A folder with any other file in it
(for example a calibration image) is loaded whole, as before. Readiness also
refuses left and right sequences that are the same files, so a folder that
matches none of the schemes cannot silently become both cameras.

> **Which camera is LEFT?** The LEFT camera is the **world reference**: its
> frame 1 is where you draw the ROI, place seeds, and preview the mesh, and its
> optical frame defines the world coordinate system (`R = I`, `T = 0`). Load the
> camera that your calibration treats as "left" (or "camera 0") here.

## Pairing and natural sort

The two folders are paired **by sort order**: the *i*-th LEFT file is matched to
the *i*-th RIGHT file. The two sequences must have the **same number of frames**.

The **Natural Sort (1, 2, …, 10)** checkbox (on by default) sorts file names
numerically, so `img2` comes before `img10`. Turn it off for strict
alphabetical order. This matters: with plain alphabetical sorting a non-zero-
padded sequence (`1, 10, 100, 11, …, 2`) is scrambled into the wrong temporal
order, silently corrupting the cumulative displacement. The setting applies to
the *next* folder load.

Frame **1** (the first file after sorting) is always the reference frame.

## The pair list

Below the drop zones, a table lists the matched pairs with three columns: **#**,
**Left**, **Right**. Rows are numbered `00`, `01`, `02`, … (0-based, matching the
frame indices used everywhere else). You can multi-select rows.

Right-clicking a selection opens a context menu:

- **Remove N selected pair(s)** — drop those pairs from the sequence.
- **Reveal in Explorer** — show the image in the system file manager: the file
  is selected in Windows Explorer and the macOS Finder; on Linux its folder
  opens.

> Removing pairs after a run exists changes the sequence, so a confirmation
> dialog (*Remove Image Pairs*) warns that the current results will be
> discarded.

## Pairing status

A status line under the list reports the pairing state:

- **No images loaded** — nothing dropped yet.
- **Paired: N frames per camera** — both cameras loaded, equal length, at least
  2 frames each. This is the ready state.
- **Mismatch: N left vs M right** — the counts differ; fix the folders so both
  cameras have the same number of frames.

The **Run** button also checks the images themselves: each camera's first and
last frames must be readable and have the same size (see
[Running](09-running.md)).

The **Next step** hint banner at the top of the sidebar walks you through what
to do next: load both folders → *Calibrate from images or import a calibration*
→ *Draw the ROI on the left camera, frame 1*.

Next: [Calibration →](04-calibration.md)

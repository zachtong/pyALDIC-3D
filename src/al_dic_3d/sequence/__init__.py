"""Sequence — ``StereoSequence`` over dual camera streams.

Two ``FrameProvider`` streams (reusing the 2D I/O protocol) plus dual mask
streams and pairing validation (count / size / filename-pattern checks).

Layer: compute (**Qt-free**).  Lands: Phase 1.  Spec: docs/architecture/01 §B.1, §E.
"""

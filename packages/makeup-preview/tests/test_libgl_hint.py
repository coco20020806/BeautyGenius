"""Tests for MediaPipe / libGL error remapping."""

from __future__ import annotations

import pytest

from makeup_preview.face_gate import reraise_if_libgl_missing


def test_reraise_if_libgl_missing_rewrites_message() -> None:
    with pytest.raises(RuntimeError, match="libGL.so.1") as ei:
        try:
            raise OSError("libGL.so.1: cannot open shared object file: No such file or directory")
        except OSError as e:
            reraise_if_libgl_missing(e)
            raise
    assert "libgl1" in str(ei.value)
    assert "install-linux-deps.sh" in str(ei.value)


def test_reraise_if_libgl_missing_ignores_other_errors() -> None:
    with pytest.raises(OSError, match="permission denied"):
        try:
            raise OSError("permission denied")
        except OSError as e:
            reraise_if_libgl_missing(e)
            raise

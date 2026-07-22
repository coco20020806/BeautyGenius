"""Align model preview output to target face geometry for before/after comparison."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from PIL import Image

from makeup_preview.config import PreviewConfig
from makeup_preview.face_landmarks import (
    create_face_landmarker,
    detect_primary_face,
    eye_midpoint,
    face_square_crop_box,
    inter_eye_distance,
)

DISPLAY_CROP_PADDING = 1.35
NEUTRAL_FILL = (245, 238, 234)


def _edge_mean_color(im: Image.Image) -> tuple[int, int, int]:
    rgb = im.convert("RGB")
    w, h = rgb.size
    pixels: list[tuple[int, int, int]] = []
    for x in range(w):
        pixels.append(rgb.getpixel((x, 0)))
        pixels.append(rgb.getpixel((x, h - 1)))
    for y in range(1, h - 1):
        pixels.append(rgb.getpixel((0, y)))
        pixels.append(rgb.getpixel((w - 1, y)))
    if not pixels:
        return NEUTRAL_FILL
    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[1] for p in pixels) // len(pixels)
    b = sum(p[2] for p in pixels) // len(pixels)
    return r, g, b


def _resize_preview_to_target(preview: Image.Image, tw: int, th: int) -> Image.Image:
    if preview.size == (tw, th):
        return preview
    return preview.resize((tw, th), Image.Resampling.LANCZOS)


def _similarity_warp_preview(
    preview: Image.Image,
    preview_geom,
    target_geom,
    canvas_size: tuple[int, int],
    fill: tuple[int, int, int],
) -> Image.Image:
    """Warp preview so preview eyes align to target eyes on target-sized canvas."""
    pw, ph = preview.size
    tw, th = canvas_size

    p_mid = eye_midpoint(preview_geom)
    t_mid = eye_midpoint(target_geom)
    p_dist = inter_eye_distance(preview_geom)
    t_dist = inter_eye_distance(target_geom)
    scale = t_dist / p_dist

    p_roll = math.radians(preview_geom.roll_deg)
    t_roll = math.radians(target_geom.roll_deg)
    theta = t_roll - p_roll
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    # Map preview pixel p -> canvas q: q = R*scale*(p - p_mid) + t_mid
    # PIL AFFINE: q = M * p + b  =>  inverse for sampling: p = inv(M)*(q - b)
    a = scale * cos_t
    b_coeff = scale * sin_t
    c = t_mid[0] - (a * p_mid[0] - b_coeff * p_mid[1])
    d = b_coeff
    e = scale * cos_t
    f = t_mid[1] - (d * p_mid[0] + e * p_mid[1])

    # PIL transform uses inverse coefficients (output -> input)
    det = a * e - b_coeff * d
    if abs(det) < 1e-8:
        return _resize_preview_to_target(preview, tw, th)
    inv_a = e / det
    inv_b = -b_coeff / det
    inv_d = -d / det
    inv_e = a / det
    inv_c = -(inv_a * c + inv_b * f)
    inv_f = -(inv_d * c + inv_e * f)

    return preview.transform(
        (tw, th),
        Image.Transform.AFFINE,
        (inv_a, inv_b, inv_c, inv_d, inv_e, inv_f),
        resample=Image.Resampling.BICUBIC,
        fillcolor=fill,
    )


def _object_position_from_crop(
    geom,
    crop_box: tuple[int, int, int, int],
) -> str:
    left, top, right, bottom = crop_box
    ex, ey = eye_midpoint(geom)
    cw = max(right - left, 1)
    ch = max(bottom - top, 1)
    px = (ex - left) / cw * 100
    py = (ey - top) / ch * 100
    px = min(100, max(0, round(px, 1)))
    py = min(100, max(0, round(py, 1)))
    return f"{px}% {py}%"


def _apply_display_crop(
    target_path: Path,
    preview_path: Path,
    target_geom,
    *,
    landmarker,
    config: PreviewConfig,
) -> tuple[tuple[int, int], str] | None:
    crop = face_square_crop_box(target_geom, padding_factor=DISPLAY_CROP_PADDING)
    left, top, right, bottom = crop
    with Image.open(target_path) as t_im, Image.open(preview_path) as p_im:
        target_rgb = t_im.convert("RGB")
        preview_rgb = p_im.convert("RGB")
        if target_rgb.size != preview_rgb.size:
            preview_rgb = preview_rgb.resize(target_rgb.size, Image.Resampling.LANCZOS)
        t_crop = target_rgb.crop((left, top, right, bottom))
        p_crop = preview_rgb.crop((left, top, right, bottom))
        display_path = target_path.parent / "target_display.jpg"
        t_crop.save(display_path, format="JPEG", quality=92)
        p_crop.save(preview_path, format="JPEG", quality=92)
        w, h = t_crop.size
    # Re-detect on display crop for object position (optional refinement)
    disp_geom = detect_primary_face(display_path, config, landmarker=landmarker)
    if disp_geom:
        obj = _object_position_from_crop(disp_geom, (0, 0, w, h))
    else:
        obj = _object_position_from_crop(target_geom, crop)
    return (w, h), obj


def harmonize_preview_pair(
    target_path: Path,
    preview_path: Path,
    config: PreviewConfig,
) -> dict[str, Any]:
    warnings: list[str] = []
    result: dict[str, Any] = {"warnings": warnings}

    if not target_path.is_file() or not preview_path.is_file():
        warnings.append("preview_align_missing_files")
        result["method"] = "skipped"
        return result

    with Image.open(target_path) as t_im, Image.open(preview_path) as p_im:
        tw, th = t_im.size
        pw, ph = p_im.size
    result["target_size"] = [tw, th]
    result["preview_size_before"] = [pw, ph]

    landmarker = create_face_landmarker(config)
    try:
        target_geom = detect_primary_face(target_path, config, landmarker=landmarker)
        preview_geom = detect_primary_face(preview_path, config, landmarker=landmarker)

        with Image.open(target_path) as t_im:
            fill = _edge_mean_color(t_im)
        with Image.open(preview_path) as p_im:
            preview_rgb = p_im.convert("RGB")

        if target_geom and preview_geom:
            aligned = _similarity_warp_preview(
                preview_rgb,
                preview_geom,
                target_geom,
                (tw, th),
                fill,
            )
            aligned.save(preview_path, format="JPEG", quality=92)
            result["method"] = "landmark_similarity"
        else:
            warnings.append("preview_align_no_face")
            resized = _resize_preview_to_target(preview_rgb, tw, th)
            resized.save(preview_path, format="JPEG", quality=92)
            result["method"] = "resize_only"
            warnings.append("preview_align_fallback_resize_only")

        if target_geom:
            crop_out = _apply_display_crop(
                target_path,
                preview_path,
                target_geom,
                landmarker=landmarker,
                config=config,
            )
            if crop_out:
                (dw, dh), obj_pos = crop_out
                result["display_crop"] = True
                result["display_size"] = [dw, dh]
                result["object_position"] = obj_pos
        else:
            warnings.append("preview_align_display_crop_skipped")
    finally:
        landmarker.close()

    return result

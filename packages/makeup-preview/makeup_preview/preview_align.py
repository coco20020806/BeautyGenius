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
    face_height,
    face_square_crop_box,
    inter_eye_distance,
)

DISPLAY_CROP_PADDING = 1.35
NEUTRAL_FILL = (245, 238, 234)
LETTERBOX_TOL = 22


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

    a = scale * cos_t
    b_coeff = scale * sin_t
    c = t_mid[0] - (a * p_mid[0] - b_coeff * p_mid[1])
    d = b_coeff
    e = scale * cos_t
    f = t_mid[1] - (d * p_mid[0] + e * p_mid[1])

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


def _is_near_fill(pixel: tuple[int, ...], fill: tuple[int, int, int], tol: int) -> bool:
    return (
        abs(pixel[0] - fill[0]) <= tol
        and abs(pixel[1] - fill[1]) <= tol
        and abs(pixel[2] - fill[2]) <= tol
    )


def _content_bbox(
    im: Image.Image,
    fill: tuple[int, int, int],
    *,
    tol: int = LETTERBOX_TOL,
) -> tuple[int, int, int, int]:
    """Tight bbox of non-fill pixels (removes warp letterbox)."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    pix = rgb.load()
    step = max(1, min(w, h) // 256)

    def row_empty(y: int) -> bool:
        for x in range(0, w, step):
            if not _is_near_fill(pix[x, y], fill, tol):
                return False
        return True

    def col_empty(x: int) -> bool:
        for y in range(0, h, step):
            if not _is_near_fill(pix[x, y], fill, tol):
                return False
        return True

    top = 0
    while top < h and row_empty(top):
        top += 1
    bottom = h - 1
    while bottom >= top and row_empty(bottom):
        bottom -= 1
    left = 0
    while left < w and col_empty(left):
        left += 1
    right = w - 1
    while right >= left and col_empty(right):
        right -= 1
    if bottom <= top or right <= left:
        return 0, 0, w, h
    return left, top, right + 1, bottom + 1


def _clamp_square_crop(
    cx: float,
    cy: float,
    side: float,
    bounds: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    bl, bt, br, bb = bounds
    max_side = min(br - bl, bb - bt)
    side = max(1.0, min(side, float(max_side)))
    half = side / 2
    left = cx - half
    top = cy - half
    right = cx + half
    bottom = cy + half
    if left < bl:
        right += bl - left
        left = bl
    if top < bt:
        bottom += bt - top
        top = bt
    if right > br:
        left -= right - br
        right = br
    if bottom > bb:
        top -= bottom - bb
        bottom = bb
    left = max(bl, int(round(left)))
    top = max(bt, int(round(top)))
    right = min(br, int(round(right)))
    bottom = min(bb, int(round(bottom)))
    side_i = min(right - left, bottom - top)
    if side_i <= 0:
        return bl, bt, br, bb
    # Keep square and prefer staying near center
    cx_i = int(round(cx))
    cy_i = int(round(cy))
    left = max(bl, min(cx_i - side_i // 2, br - side_i))
    top = max(bt, min(cy_i - side_i // 2, bb - side_i))
    return left, top, left + side_i, top + side_i


def _zoom_pair_around_center(
    target: Image.Image,
    preview: Image.Image,
    center: tuple[float, float],
    scale: float,
) -> tuple[Image.Image, Image.Image, tuple[float, float]]:
    """Scale both images about center, then crop back to original canvas size."""
    tw, th = target.size
    if scale <= 1.001:
        return target, preview, center
    nw = max(tw, int(round(tw * scale)))
    nh = max(th, int(round(th * scale)))
    t2 = target.resize((nw, nh), Image.Resampling.LANCZOS)
    p2 = preview.resize((nw, nh), Image.Resampling.LANCZOS)
    cx, cy = center[0] * (nw / tw), center[1] * (nh / th)
    left = int(round(cx - tw / 2))
    top = int(round(cy - th / 2))
    left = max(0, min(left, nw - tw))
    top = max(0, min(top, nh - th))
    box = (left, top, left + tw, top + th)
    return t2.crop(box), p2.crop(box), (cx - left, cy - top)


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
    fill: tuple[int, int, int],
) -> tuple[tuple[int, int], str, float] | None:
    """
    Build same-size display pair that fills the frame:
    remove warp letterbox, crop by the *smaller* face so it fills, zoom both equally.
    """
    with Image.open(target_path) as t_im, Image.open(preview_path) as p_im:
        target_rgb = t_im.convert("RGB")
        preview_rgb = p_im.convert("RGB")
        if target_rgb.size != preview_rgb.size:
            preview_rgb = preview_rgb.resize(target_rgb.size, Image.Resampling.LANCZOS)
        w, h = target_rgb.size

    # Re-detect after warp so face sizes reflect aligned images
    aligned_target_geom = detect_primary_face(target_path, config, landmarker=landmarker) or target_geom
    aligned_preview_geom = detect_primary_face(preview_path, config, landmarker=landmarker)

    center = eye_midpoint(aligned_target_geom)
    fill_scale = 1.0

    # Match face scale: zoom BOTH around eyes so the smaller face reaches the larger.
    # Keeps eye alignment while eliminating one-big-one-small in the frame.
    if aligned_preview_geom:
        t_eye = inter_eye_distance(aligned_target_geom)
        p_eye = inter_eye_distance(aligned_preview_geom)
        match_scale = max(t_eye, p_eye) / min(t_eye, p_eye)
        if match_scale > 1.02:
            target_rgb, preview_rgb, center = _zoom_pair_around_center(
                target_rgb, preview_rgb, center, match_scale
            )
            fill_scale *= match_scale
            tmp_t = target_path.parent / "_tmp_target_fill.jpg"
            tmp_p = target_path.parent / "_tmp_preview_fill.jpg"
            target_rgb.save(tmp_t, format="JPEG", quality=92)
            preview_rgb.save(tmp_p, format="JPEG", quality=92)
            try:
                aligned_target_geom = (
                    detect_primary_face(tmp_t, config, landmarker=landmarker) or aligned_target_geom
                )
                aligned_preview_geom = (
                    detect_primary_face(tmp_p, config, landmarker=landmarker) or aligned_preview_geom
                )
                center = eye_midpoint(aligned_target_geom)
            finally:
                tmp_t.unlink(missing_ok=True)
                tmp_p.unlink(missing_ok=True)

    # Remove warp letterbox only when margins are clearly fill-colored and substantial
    content = _content_bbox(preview_rgb, fill)
    cl, ct, cr, cb = content
    cw, ch = max(cr - cl, 1), max(cb - ct, 1)
    margin_frac = 1.0 - min(cw / w, ch / h)
    letterbox_scale = max(w / cw, h / ch)
    if margin_frac >= 0.04 and letterbox_scale > 1.04:
        target_rgb, preview_rgb, center = _zoom_pair_around_center(
            target_rgb, preview_rgb, center, letterbox_scale
        )
        fill_scale *= letterbox_scale
        tmp_t = target_path.parent / "_tmp_target_fill.jpg"
        tmp_p = target_path.parent / "_tmp_preview_fill.jpg"
        target_rgb.save(tmp_t, format="JPEG", quality=92)
        preview_rgb.save(tmp_p, format="JPEG", quality=92)
        try:
            aligned_target_geom = (
                detect_primary_face(tmp_t, config, landmarker=landmarker) or aligned_target_geom
            )
            aligned_preview_geom = (
                detect_primary_face(tmp_p, config, landmarker=landmarker) or aligned_preview_geom
            )
            center = eye_midpoint(aligned_target_geom)
        finally:
            tmp_t.unlink(missing_ok=True)
            tmp_p.unlink(missing_ok=True)
        content = (0, 0, w, h)

    # Crop side driven by the *smaller* face so it fills the display frame
    t_face_h = face_height(aligned_target_geom)
    p_face_h = face_height(aligned_preview_geom) if aligned_preview_geom else t_face_h
    min_face_h = min(t_face_h, p_face_h)
    face_side = min_face_h * DISPLAY_CROP_PADDING

    target_box = face_square_crop_box(aligned_target_geom, padding_factor=DISPLAY_CROP_PADDING)
    target_side = max(target_box[2] - target_box[0], 1)
    side = min(face_side, float(target_side))

    crop = _clamp_square_crop(center[0], center[1], side, content)
    left, top, right, bottom = crop
    crop_side = right - left
    if crop_side <= 0:
        return None

    # Extra shared zoom if smaller face still under-fills the crop
    face_fill = min_face_h / crop_side
    desired_fill = 1.0 / DISPLAY_CROP_PADDING
    if face_fill < desired_fill * 0.92:
        zoom = min(desired_fill / max(face_fill, 1e-6), 1.85)
        expanded = crop_side / zoom
        crop = _clamp_square_crop(center[0], center[1], expanded, content)
        left, top, right, bottom = crop
        fill_scale *= zoom

    t_crop = target_rgb.crop((left, top, right, bottom))
    p_crop = preview_rgb.crop((left, top, right, bottom))
    out_side = max(t_crop.size[0], t_crop.size[1], 1)
    if t_crop.size != (out_side, out_side):
        t_crop = t_crop.resize((out_side, out_side), Image.Resampling.LANCZOS)
    if p_crop.size != (out_side, out_side):
        p_crop = p_crop.resize((out_side, out_side), Image.Resampling.LANCZOS)

    display_path = target_path.parent / "target_display.jpg"
    preview_display_path = target_path.parent / "preview_display.jpg"
    t_crop.save(display_path, format="JPEG", quality=92)
    p_crop.save(preview_display_path, format="JPEG", quality=92)

    disp_geom = detect_primary_face(display_path, config, landmarker=landmarker)
    if disp_geom:
        obj = _object_position_from_crop(disp_geom, (0, 0, out_side, out_side))
    else:
        obj = _object_position_from_crop(aligned_target_geom, crop)
    return (out_side, out_side), obj, fill_scale


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
                fill=fill,
            )
            if crop_out:
                (dw, dh), obj_pos, fill_scale = crop_out
                result["display_crop"] = True
                result["display_size"] = [dw, dh]
                result["object_position"] = obj_pos
                result["display_fill_scale"] = round(fill_scale, 4)
            else:
                warnings.append("preview_align_display_crop_failed")
        else:
            warnings.append("preview_align_display_crop_skipped")

        with Image.open(target_path) as t_im, Image.open(preview_path) as p_im:
            tw, th = t_im.size
            if p_im.size != (tw, th):
                _resize_preview_to_target(p_im.convert("RGB"), tw, th).save(
                    preview_path, format="JPEG", quality=92
                )
                warnings.append("preview_align_size_corrected")
        result["preview_size_after"] = list(Image.open(preview_path).size)
    finally:
        landmarker.close()

    return result

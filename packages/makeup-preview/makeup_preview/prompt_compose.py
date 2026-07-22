"""Compose full transfer prompt text (base + optional scoped appendix)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from makeup_preview.prompt_loader import Layout, load_scope_appendix, load_transfer_prompt
from makeup_preview.scope_loader import TransferScope, scope_to_preview_dict


@dataclass(frozen=True)
class ComposedTransferPrompt:
    text: str
    prompt_text_version: str
    used_fallback: bool
    prompt_mode: str
    scope: dict[str, object] | None


def _join_zh(items: tuple[str, ...]) -> str:
    return "、".join(items) if items else ""


def _fill_appendix(template: str, scope: TransferScope) -> str:
    primary = _join_zh(scope.application_primaries)
    region = _join_zh(scope.allowed_region_labels) or primary
    return (
        template.replace("{{PRIMARY_LIST_ZH}}", primary)
        .replace("{{REGION_LIST_ZH}}", region)
    )


def compose_transfer_prompt(
    skill_dir: Path,
    *,
    layout: Layout,
    transfer_scope: TransferScope,
) -> ComposedTransferPrompt:
    loaded = load_transfer_prompt(skill_dir, layout=layout)
    text = loaded.text
    mode = transfer_scope.prompt_mode
    used_fallback = loaded.used_fallback
    scope_doc: dict[str, object] | None = None

    if mode == "scoped" and transfer_scope.application_primaries:
        appendix_loaded = load_scope_appendix(skill_dir, layout=layout)
        used_fallback = used_fallback or appendix_loaded.used_fallback
        appendix = _fill_appendix(appendix_loaded.text, transfer_scope)
        text = f"{text.rstrip()}\n\n{appendix.lstrip()}"
        scope_doc = scope_to_preview_dict(transfer_scope)
    elif transfer_scope.source != "default_full" or transfer_scope.present_primaries:
        scope_doc = scope_to_preview_dict(transfer_scope)

    return ComposedTransferPrompt(
        text=text,
        prompt_text_version=loaded.prompt_text_version,
        used_fallback=used_fallback,
        prompt_mode=mode,
        scope=scope_doc,
    )

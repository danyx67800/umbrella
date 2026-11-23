"""Motore di integrazione fail-closed.

Ogni operazione dichiara un anchor esatto e un marker di idempotenza. Se
l'anchor non compare esattamente una volta, l'operazione fallisce invece di
applicare una modifica approssimativa.
"""

from __future__ import annotations

import dataclasses
import hashlib
import re
from pathlib import Path
from typing import Sequence


class IntegrationError(RuntimeError):
    """Errore bloccante di integrazione."""


@dataclasses.dataclass(frozen=True, kw_only=True)
class Operation:
    file: str
    marker: str
    description: str = ""


@dataclasses.dataclass(frozen=True, kw_only=True)
class InsertAfter(Operation):
    anchor: str
    text: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class InsertBefore(Operation):
    anchor: str
    text: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class Replace(Operation):
    old: str
    new: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class RegexReplace(Operation):
    pattern: str
    replacement: str
    min_count: int = 1
    max_count: int | None = None
    flags: int = re.MULTILINE


@dataclasses.dataclass(frozen=True, kw_only=True)
class GnListAdd(Operation):
    target: str
    list_name: str
    value: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class ReplaceFile(Operation):
    content: str
    expected_sha256: str | None = None


@dataclasses.dataclass(frozen=True)
class Result:
    operation: str
    file: str
    status: str
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {"applied", "ok", "skipped"}

    @property
    def changed(self) -> bool:
        return self.status == "applied"


_APPLIED = "applied"
_OK = "ok"
_SKIPPED = "skipped"
_ERROR = "error"


def _read(path: Path) -> str:
    if not path.is_file():
        raise IntegrationError(f"file non trovato: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _write(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def _single_anchor(text: str, anchor: str, file: str) -> int:
    count = text.count(anchor)
    if count != 1:
        raise IntegrationError(
            f"{file}: anchor trovato {count} volte (atteso 1): "
            f"{anchor[:120]!r}")
    return count


def _find_target_block(text: str, header: str, file: str) -> tuple[int, int]:
    count = text.count(header)
    if count != 1:
        raise IntegrationError(
            f"{file}: target {header!r} trovato {count} volte (atteso 1)")
    start = text.index(header)
    brace = text.find("{", start)
    if brace < 0:
        raise IntegrationError(f"{file}: target {header!r} senza blocco")

    depth = 0
    in_string = False
    index = brace
    while index < len(text):
        char = text[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "#":
            newline = text.find("\n", index)
            index = len(text) if newline < 0 else newline
            continue
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return brace, index
        index += 1
    raise IntegrationError(f"{file}: blocco GN non bilanciato per {header!r}")


def _gn_list_insert(text: str, operation: GnListAdd) -> tuple[str, str]:
    block_start, block_end = _find_target_block(
        text, operation.target, operation.file)
    pattern = re.compile(
        rf"(?m)^(?P<indent>[ \t]*){re.escape(operation.list_name)}"
        rf"\s*=\s*\[")
    match = pattern.search(text, block_start, block_end)
    if not match:
        raise IntegrationError(
            f"{operation.file}: lista {operation.list_name!r} assente nel "
            f"target {operation.target!r}")
    bracket = text.find("[", match.start(), match.end())
    if bracket < 0:
        raise IntegrationError(
            f"{operation.file}: lista {operation.list_name!r} non valida")

    quoted = f'"{operation.value}"'
    if quoted in text[block_start:block_end]:
        return text, _SKIPPED

    after = text[bracket + 1:bracket + 400]
    indent_match = re.match(r"\s*\n(?P<indent>[ \t]+)\"", after)
    indent = indent_match.group("indent") if indent_match else "    "
    addition = f'\n{indent}{quoted},'
    return text[:bracket + 1] + addition + text[bracket + 1:], _APPLIED


def _apply_one(src: Path, operation: Operation, check: bool) -> Result:
    path = src / operation.file
    text = _read(path)

    # GnListAdd verifica il duplicato dentro il target: il marker globale
    # potrebbe trovarsi in un altro target dello stesso BUILD.gn.
    if (operation.marker and not isinstance(operation, GnListAdd) and
            operation.marker in text):
        return Result(
            type(operation).__name__, operation.file, _SKIPPED,
            "già integrato (marker presente)")

    if isinstance(operation, InsertAfter):
        _single_anchor(text, operation.anchor, operation.file)
        updated = text.replace(operation.anchor, operation.anchor +
                               operation.text, 1)
    elif isinstance(operation, InsertBefore):
        _single_anchor(text, operation.anchor, operation.file)
        updated = text.replace(operation.anchor, operation.text +
                               operation.anchor, 1)
    elif isinstance(operation, Replace):
        try:
            _single_anchor(text, operation.old, operation.file)
        except IntegrationError:
            if operation.new and operation.new in text:
                return Result(
                    type(operation).__name__, operation.file, _SKIPPED,
                    "già integrato (testo nuovo presente)")
            raise
        updated = text.replace(operation.old, operation.new, 1)
    elif isinstance(operation, RegexReplace):
        compiled = re.compile(operation.pattern, operation.flags)
        matches = compiled.findall(text)
        count = len(matches)
        if count < operation.min_count or (
                operation.max_count is not None and
                count > operation.max_count):
            raise IntegrationError(
                f"{operation.file}: regex trovata {count} volte "
                f"(attese {operation.min_count}..{operation.max_count})")
        updated = compiled.sub(operation.replacement, text)
    elif isinstance(operation, GnListAdd):
        updated, status = _gn_list_insert(text, operation)
        if status == _SKIPPED:
            return Result(
                type(operation).__name__, operation.file, _SKIPPED,
                f"{operation.list_name!r} contiene già {operation.value!r}")
    elif isinstance(operation, ReplaceFile):
        if operation.expected_sha256:
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if digest != operation.expected_sha256:
                raise IntegrationError(
                    f"{operation.file}: sha256 upstream inatteso "
                    f"{digest[:12]}… (atteso "
                    f"{operation.expected_sha256[:12]}…)")
        updated = operation.content
    else:
        raise IntegrationError(
            f"operazione sconosciuta: {type(operation).__name__}")

    if updated == text:
        return Result(type(operation).__name__, operation.file, _OK,
                      "nessuna modifica necessaria")
    if check:
        return Result(type(operation).__name__, operation.file, _OK,
                      "anchor valido (check-only)")
    _write(path, updated)
    return Result(type(operation).__name__, operation.file, _APPLIED)


def apply_operations(
    src: Path,
    operations: Sequence[Operation],
    *,
    check: bool = False,
) -> list[Result]:
    """Applica o verifica le operazioni. Non solleva sui singoli errori."""

    results: list[Result] = []
    for operation in operations:
        try:
            results.append(_apply_one(src, operation, check))
        except IntegrationError as error:
            results.append(Result(
                type(operation).__name__, operation.file, _ERROR, str(error)))
        except OSError as error:
            results.append(Result(
                type(operation).__name__, operation.file, _ERROR,
                f"I/O: {error}"))
    return results


def describe_operations(operations: Sequence[Operation]) -> list[str]:
    lines = []
    for operation in operations:
        detail = f"target={operation.target!r} " if isinstance(
            operation, GnListAdd) else ""
        lines.append(
            f"{type(operation).__name__}: {operation.file} "
            f"({detail}{operation.description})")
    return lines

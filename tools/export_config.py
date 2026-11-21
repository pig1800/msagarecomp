"""Generate symbols/functions.csv and config.toml from static analysis JSON/CSV."""

from __future__ import annotations

import csv
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANALYSIS_OUT = ROOT / "analysis_out"
SYMBOLS_DIR = ROOT / "symbols"

EXTRA_STUBS = {
    0x0028E168: "sceGsResetPath",
    0x0028E208: "sceGsSyncPath",
}


def export_symbols_csv() -> pathlib.Path:
    SYMBOLS_DIR.mkdir(parents=True, exist_ok=True)
    src_csv = ANALYSIS_OUT / "ps2recomp_functions.csv"
    dst_csv = SYMBOLS_DIR / "functions.csv"

    rows = []
    with src_csv.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            start = int(row["Start"], 16)
            if start in EXTRA_STUBS:
                row["Name"] = EXTRA_STUBS[start]
            rows.append(row)

    with dst_csv.open("w", encoding="utf-8", newline="\n") as fh:
        writer = csv.DictWriter(fh, fieldnames=["Name", "Start", "End", "Size"])
        writer.writeheader()
        writer.writerows(rows)

    return dst_csv


def parse_existing_stubs(src_toml: pathlib.Path) -> list[str]:
    text = src_toml.read_text(encoding="utf-8")
    stubs: dict[int, str] = {}
    for match in re.finditer(r'"([A-Za-z0-9_]+)@(0x[0-9A-Fa-f]+)"', text):
        name, addr_s = match.group(1), match.group(2)
        stubs[int(addr_s, 16)] = f"{name}@0x{int(addr_s, 16):08X}"
    for addr, name in EXTRA_STUBS.items():
        stubs[addr] = f"{name}@0x{addr:08X}"
    return sorted(stubs.values(), key=lambda item: (item.split("@")[0], int(item.split("@")[1], 16)))


def export_config_toml() -> pathlib.Path:
    stubs = parse_existing_stubs(ANALYSIS_OUT / "config.toml")
    jump_tables = json.loads((ANALYSIS_OUT / "jumptables.json").read_text(encoding="utf-8"))

    lines: list[str] = [
        "# PS2Recomp static recompilation manifest for ps2xRuntime",
        "[general]",
        'input = "./runtime_data/SLPM_742.26"',
        'ghidra_output = "./symbols/functions.csv"',
        'output = "./generated"',
        "single_file_output = false",
        "low_memory_mode = false",
        "output_worker_threads = 0",
        "patch_syscalls = false",
        "patch_cop0 = false",
        "patch_cache = false",
        "stubs = [",
    ]
    for entry in stubs:
        lines.append(f'    "{entry}",')
    lines.extend([
        "]",
        "skip = []",
        "",
        "[patches]",
        "instructions = []",
        "",
    ])

    emitted_tables = 0
    seen_table_addrs: set[int] = set()
    for jt in jump_tables:
        table_addr = int(jt["table_addr"], 16)
        targets = jt.get("targets") or []
        if not targets or table_addr in seen_table_addrs:
            continue
        seen_table_addrs.add(table_addr)
        lines.append("[[jump_tables.table]]")
        lines.append(f'address = "0x{table_addr:08X}"')
        lines.append("base_register = 0")
        entry_items = ", ".join(
            f'{{ index = {idx}, target = "0x{int(tgt, 16):08X}" }}'
            for idx, tgt in enumerate(targets)
        )
        lines.append(f"entries = [{entry_items}]")
        lines.append("")
        emitted_tables += 1

    dst_toml = ROOT / "config.toml"
    dst_toml.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(stubs)} stubs and {emitted_tables} jump tables to {dst_toml}")
    return dst_toml


if __name__ == "__main__":
    csv_path = export_symbols_csv()
    toml_path = export_config_toml()
    print(f"Wrote {csv_path} and {toml_path}")

"""Run a bounded headless smoke test of ps2_host_runtime and write tests/traces/boot_trace.log."""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_EXE = ROOT / "build" / "runtime" / "ps2_host_runtime.exe"
DEFAULT_ELF = ROOT / "runtime_data" / "SLPM_742.26"
DEFAULT_OUT = ROOT / "tests" / "traces" / "boot_trace.log"


def run_smoke(exe: pathlib.Path, elf: pathlib.Path, out_path: pathlib.Path, timeout_s: float, max_lines: int) -> int:
    if not exe.exists():
        print(f"ERROR: Runtime executable not found: {exe}", file=sys.stderr)
        return 2
    if not elf.exists():
        print(f"ERROR: Runtime ELF not found: {elf}", file=sys.stderr)
        return 2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    timed_out = False

    proc = subprocess.Popen(
        [str(exe), str(elf)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    try:
        raw_output, _ = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        raw_output, _ = proc.communicate()

    elapsed = time.monotonic() - start
    exit_code = proc.returncode

    raw_lines = raw_output.splitlines()

    # Collapse consecutive identical lines to keep the trace concise (< max_lines)
    # while preserving exact first-occurrence ordering and repeat counts.
    compacted: list[str] = []
    prev: str | None = None
    repeat_count = 0

    def flush_repeat() -> None:
        nonlocal repeat_count
        if repeat_count > 0:
            compacted.append(f"  [... repeated {repeat_count} more time(s) ...]")
            repeat_count = 0

    for line in raw_lines:
        if prev is not None and line == prev:
            repeat_count += 1
            continue
        flush_repeat()
        compacted.append(line)
        prev = line
    flush_repeat()

    header = [
        "# ps2xRuntime Deterministic Boot Smoke Trace",
        f"# executable: {exe.relative_to(ROOT).as_posix()}",
        f"# target_elf: {elf.relative_to(ROOT).as_posix()}",
        f"# timeout_s: {timeout_s:.1f}",
        f"# elapsed_s: {elapsed:.2f}",
        f"# outcome: {'timeout_bounded_stop' if timed_out else f'exited(code={exit_code})'}",
        f"# raw_lines: {len(raw_lines)}, compacted_lines: {len(compacted)}",
        "# ------------------------------------------------------------",
    ]

    budget = max(10, max_lines - len(header) - 2)
    if len(compacted) > budget:
        head_n = budget * 2 // 3
        tail_n = budget - head_n
        body = (
            compacted[:head_n]
            + [f"# [... truncated {len(compacted) - head_n - tail_n} middle line(s) ...]"]
            + compacted[-tail_n:]
        )
    else:
        body = compacted

    final_lines = header + body
    out_path.write_text("\n".join(final_lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(final_lines)} lines to {out_path} (outcome={header[5].split(': ', 1)[1]})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=pathlib.Path, default=DEFAULT_EXE)
    parser.add_argument("--elf", type=pathlib.Path, default=DEFAULT_ELF)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--timeout", type=float, default=4.0)
    parser.add_argument("--max-lines", type=int, default=450)
    args = parser.parse_args()
    return run_smoke(args.exe, args.elf, args.out, args.timeout, args.max_lines)


if __name__ == "__main__":
    raise SystemExit(main())

# CLAUDE.md — C++20 PS2 Host Compatibility Runtime (`ps2xRuntime`)

## Workspace Scope & Identity

This repository is a **C++20 PlayStation 2 Emotion Engine (R5900) / Graphics Synthesizer (GS) / VIF1 / VU1 / SPU2 host compatibility runtime** bootstrapped on `ps2xRuntime` and `ps2xIOP`.

### Final Goal: Pure Native PC Executable
The end goal is a **pure, standalone, high-performance native PC executable** (Windows primary, portable to Linux/macOS):
- **Graphics Backend:** **Vulkan** native GPU-accelerated GS/VIF1/VU1 rendering pipeline (migrating away from the initial `raylib`/OpenGL CPU-rasterized `ps2xRuntime` bootstrap).
- **Audio Backend:** **Native OS audio APIs** (**WASAPI** on Windows; native equivalents such as PipeWire/PulseAudio/ALSA on Linux and CoreAudio on macOS) for low-latency SPU2/ADPCM/streaming output.
- **Platform / Input / Windowing:** Native PC windowing, swapchain presentation, gamepad/keyboard input, and host filesystem/save persistence behind clean C++20 platform interfaces under `src/runtime/`.
- **Future Portability:** Keep OS/graphics/audio boundaries cleanly abstracted so future ports (such as Android) remain feasible later, **but omit non-PC port work for now** and focus strictly on native PC.

### Engineering Progression
1. **Stage 1 — Execution Bring-Up:** Use the compiling `ps2xRuntime` + `ps2xIOP` baseline to unblock cold boot, EE kernel syscalls, IOP RPCs, VFS/CDVD loading, and clean-room `src/overrides/` hooks.
2. **Stage 2 — Native PC Architecture:** Introduce clean backend interfaces under `src/runtime/` and replace the temporary `raylib`/software-GS bootstrap with a **native Vulkan renderer**, **native WASAPI (Windows) / OS audio backend**, and native PC input/windowing for a pure native PC executable.

Focus strictly on C++20 systems, hardware emulation, graphics, audio, and runtime compatibility engineering:
- EE kernel syscalls, threading/semaphores/event flags, and HLE SDK shims (`src/runtime/`, `PS2Recomp/ps2xRuntime/`)
- DMAC / GIF / VIF1 packet parsing, **Vulkan GS hardware rendering**, and VU1 microprogram execution
- SPU2 mixing over **native OS audio APIs (WASAPI on Windows)**, IOP RPC transport, and virtual filesystem (`ps2_vfs`) compatibility
- Clean-room C++20 function overrides under `src/overrides/` registered with `PS2_REGISTER_GAME_OVERRIDE`

## Hard Rules

1. **Treat `generated/` as STRICTLY READ-ONLY compiler output.**
   - Never manually edit files inside `generated/`. They are deterministically emitted by `ps2_recomp` from `config.toml` and `symbols/functions.csv`.
   - To replace, intercept, or fix behavior at a guest address, either:
     - Add a clean, idiomatic, commented C++20 override in `src/overrides/` bound via `PS2_REGISTER_GAME_OVERRIDE` / `ps2_game_overrides::bindAddressHandler(...)` or `runtime.registerFunction(addr, fn)`, OR
     - Update a runtime HLE stub/syscall in `src/runtime/` or `PS2Recomp/ps2xRuntime/`.
2. **Never read, inspect, or index `./runtime_data/` or raw binary disc assets.**
   - `.claude/settings.json` explicitly blocks `Read(./runtime_data/**)` and raw binary extensions.
   - Only pass `./runtime_data/SLPM_742.26` as a CLI argument when executing the compiled host binary for smoke tests.
3. **Keep `src/` clean-room C++20.**
   - Write idiomatic C++20 functions describing high-level host/hardware semantics—never paste raw MIPS assembly dumps or register-by-register transliterations into `src/`.
4. **Always start from the deterministic runtime trace.**
   - Read `tests/traces/boot_trace.log` to identify the exact guest PC, call site, or unimplemented hardware/syscall/IOP RPC boundary where execution currently halts.

## Repository Layout

| Path | Ownership | Purpose |
|---|---|---|
| `src/runtime/` | Editable (C++20) | Host compatibility shims, diagnostics, GS/VU1/SPU2/IO extensions |
| `src/overrides/` | Editable (C++20) | Build-scoped `PS2_REGISTER_GAME_OVERRIDE` hooks |
| `include/` | Editable (C++20) | Public headers for `src/runtime/` and `src/overrides/` |
| `PS2Recomp/ps2xRuntime/` | Upstream runtime | Core EE/GS/VU1/SPU2/Kernel runtime library (`ps2_runtime`) |
| `PS2Recomp/ps2xIOP/` | Upstream IOP | Virtual IOP / IRX execution and RPC fallback layer (`ps2_iop`) |
| `config.toml` | Declarative config | SDK stub bindings (`handler@0xADDR`) and jump-table manifest |
| `symbols/functions.csv` | Symbol boundary map | Function entry/end table consumed by `ps2_recomp` |
| `generated/` | **READ-ONLY** (gitignored) | Statically lifted C++20 translation units + `register_functions.cpp` |
| `tests/traces/boot_trace.log` | Trace artifact | Reproducible headless boot trace (<500 lines) |

## Build & Verification Commands

Run inside a Visual Studio x64 Developer Command Prompt (`VsDevCmd.bat -arch=amd64 -host_arch=amd64`):

```powershell
# Incremental host runtime build
cmake --build build/runtime --target ps2_host_runtime

# Re-run deterministic headless smoke trace (~3-5s bounded)
.\build\runtime\ps2_host_runtime.exe .\runtime_data\SLPM_742.26
```

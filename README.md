# PS2 Emotion Engine Host Compatibility Runtime (`ps2xRuntime`)

A **C++20 PlayStation 2 Emotion Engine (R5900), Graphics Synthesizer (GS), VIF1/VU1, and SPU2 host compatibility runtime** built on [`PS2Recomp`](PS2Recomp/) (`ps2xRuntime` + `ps2xIOP`).

## Architecture

- **`PS2Recomp/`** (submodule): Core static R5900-to-C++20 lifter (`ps2xRecomp`), EE/GS/VU1/SPU2 host runtime (`ps2xRuntime`), and virtual IOP/IRX execution engine (`ps2xIOP`).
- **`src/runtime/` & `include/`**: Host-side C++20 compatibility shims, DMA/GIF/VIF1/GS helpers, SPU2 audio glue, and trace diagnostics.
- **`src/overrides/`**: Build-scoped runtime function overrides registered via `PS2_REGISTER_GAME_OVERRIDE` (clean, idiomatic C++20 implementations).
- **`config.toml` & `symbols/functions.csv`**: Declarative static-recompilation manifest specifying SDK syscall/stub bindings (`handler@0xADDR`) and switch jump tables.
- **`generated/`** *(gitignored, read-only)*: Deterministic C++20 translation units and function dispatch table (`register_functions.cpp`) emitted locally by `ps2_recomp`.
- **`runtime_data/`** *(gitignored)*: Local user-supplied runtime media directory used only when launching the compiled host binary.
- **`tests/traces/`**: Reproducible runtime execution traces (`boot_trace.log`) documenting current bring-up progress and next unimplemented hardware/syscall boundaries.

## Quick Start (Windows / MSVC C++20 + Ninja)

From a Visual Studio 2022/2026 x64 Developer Command Prompt:

```powershell
# 1. Build the static lifter (one-time)
cmake -S PS2Recomp -B build/recomp -G Ninja -DCMAKE_BUILD_TYPE=Release `
  -DPS2X_BUILD_RECOMP=ON -DPS2X_BUILD_RUNTIME=OFF -DPS2X_BUILD_ANALYZER=OFF `
  -DPS2X_BUILD_TEST=OFF -DPS2X_BUILD_STUDIO=OFF
cmake --build build/recomp --target ps2_recomp

# 2. Emit generated/ C++20 translation units from local ./runtime_data/
.\build\recomp\ps2xRecomp\ps2_recomp.exe .\config.toml

# 3. Configure and build the C++20 host runtime executable
cmake -S . -B build/runtime -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/runtime --target ps2_host_runtime

# 4. Run against local ./runtime_data/<ELF>
.\build\runtime\ps2_host_runtime.exe .\runtime_data\SLPM_742.26
```

## License

All first-party source code in `src/`, `include/`, `tools/`, `CMakeLists.txt`, and `config.toml` is licensed under the [MIT License](LICENSE). Third-party runtime components under `PS2Recomp/` retain their upstream license.

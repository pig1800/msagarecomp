#include "game_overrides.h"
#include "runtime_shims.h"

#include "ps2_runtime.h"

#include <iostream>

namespace
{
    constexpr uint32_t kTargetEntryPoint = 0x00287250u;
    constexpr uint32_t kTargetElfCrc32 = 0x7EFB6E00u;

    void applyTargetOverrides(PS2Runtime &runtime)
    {
        std::cout << "[overrides] Applying build-scoped ps2xRuntime bindings for SLPM_742.26 (entry=0x"
                  << std::hex << kTargetEntryPoint << std::dec << ")" << std::endl;

        // Ensure critical libgraph path synchronization routines remain wired to host stubs.
        ps2_game_overrides::bindAddressHandler(runtime, 0x0028E168u, "sceGsResetPath");
        ps2_game_overrides::bindAddressHandler(runtime, 0x0028E208u, "sceGsSyncPath");

        ps2_host_shims::registerHostShims(runtime);
    }
}

PS2_REGISTER_GAME_OVERRIDE(
    "slpm_742_26_runtime_overrides",
    "SLPM_742.26",
    kTargetEntryPoint,
    kTargetElfCrc32,
    &applyTargetOverrides)

#pragma once

#include <cstdint>

class PS2Runtime;

namespace ps2_host_shims
{
    // Install any additional host-side runtime compatibility hooks or trace diagnostics.
    void registerHostShims(PS2Runtime &runtime);
}

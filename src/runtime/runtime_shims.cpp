#include "runtime_shims.h"

#include "ps2_runtime.h"

#include <iostream>

namespace ps2_host_shims
{
    void registerHostShims(PS2Runtime &runtime)
    {
        (void)runtime;
        std::cout << "[ps2_host_shims] Host compatibility runtime hooks ready." << std::endl;
    }
}

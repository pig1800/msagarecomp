cmake_minimum_required(VERSION 3.21)

project(ps2_host_runtime VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(PS2HOST_ENABLE_UNITY_BUILD "Build lifted translation units with CMake unity batching" ON)
set(PS2HOST_UNITY_BATCH_SIZE 64 CACHE STRING "Unity build batch size for ps2_host_runtime")
option(PS2HOST_ENABLE_PCH "Enable precompiled headers for ps2_host_runtime" ON)

# Build only the runtime and IOP modules from PS2Recomp by default.
set(PS2X_BUILD_RECOMP OFF CACHE BOOL "Build ps2xRecomp" FORCE)
set(PS2X_BUILD_ANALYZER OFF CACHE BOOL "Build ps2xAnalyzer" FORCE)
set(PS2X_BUILD_TEST OFF CACHE BOOL "Build ps2xTest" FORCE)
set(PS2X_BUILD_STUDIO OFF CACHE BOOL "Build ps2xStudio" FORCE)
set(PS2X_BUILD_RUNTIME ON CACHE BOOL "Build ps2xRuntime" FORCE)

add_subdirectory(PS2Recomp)

set(GENERATED_DIR "${CMAKE_CURRENT_SOURCE_DIR}/generated")
if(NOT EXISTS "${GENERATED_DIR}/register_functions.cpp")
    message(FATAL_ERROR
        "Missing ${GENERATED_DIR}/register_functions.cpp. "
        "Run ps2_recomp config.toml first to emit generated/ translation units.")
endif()

file(GLOB GENERATED_SRC_FILES CONFIGURE_DEPENDS
    "${GENERATED_DIR}/*.cpp"
)

file(GLOB_RECURSE HOST_RUNTIME_SRC_FILES CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/runtime/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/overrides/*.cpp"
)

set(PS2_RUNTIME_MAIN "${CMAKE_CURRENT_SOURCE_DIR}/PS2Recomp/ps2xRuntime/src/main.cpp")

add_executable(ps2_host_runtime
    "${PS2_RUNTIME_MAIN}"
    ${HOST_RUNTIME_SRC_FILES}
    ${GENERATED_SRC_FILES}
)

target_include_directories(ps2_host_runtime PRIVATE
    "${GENERATED_DIR}"
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

target_link_libraries(ps2_host_runtime PRIVATE
    ps2_runtime
)

if(PS2X_ENABLE_DEBUG_UI AND NOT PS2X_IS_VITA AND NOT PS2X_IS_ANDROID)
    target_sources(ps2_host_runtime PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/PS2Recomp/ps2xRuntime/src/lib/ps2_debug_panel.cpp"
    )
    target_link_libraries(ps2_host_runtime PRIVATE rlImGui imgui)
    target_compile_definitions(ps2_host_runtime PRIVATE PS2X_ENABLE_DEBUG_UI=1)
endif()

if(PS2HOST_ENABLE_UNITY_BUILD)
    set_target_properties(ps2_host_runtime PROPERTIES
        UNITY_BUILD ON
        UNITY_BUILD_BATCH_SIZE "${PS2HOST_UNITY_BATCH_SIZE}"
    )
    set_source_files_properties(
        "${PS2_RUNTIME_MAIN}"
        ${HOST_RUNTIME_SRC_FILES}
        "${GENERATED_DIR}/register_functions.cpp"
        PROPERTIES SKIP_UNITY_BUILD_INCLUSION TRUE
    )
endif()

if(PS2HOST_ENABLE_PCH)
    set(PS2HOST_PCH_HEADERS
        "${CMAKE_CURRENT_SOURCE_DIR}/PS2Recomp/ps2xRuntime/include/ps2_runtime_macros.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/PS2Recomp/ps2xRuntime/include/ps2_runtime.h"
        "${GENERATED_DIR}/ps2_recompiled_functions.h"
        "${GENERATED_DIR}/ps2_recompiled_stubs.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/PS2Recomp/ps2xRuntime/include/ps2_syscalls.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/PS2Recomp/ps2xRuntime/include/ps2_stubs.h"
    )
    target_precompile_headers(ps2_host_runtime PRIVATE ${PS2HOST_PCH_HEADERS})
endif()

if(MSVC)
    target_compile_options(ps2_host_runtime PRIVATE /FS /bigobj)
    target_link_options(ps2_host_runtime PRIVATE "/FORCE:MULTIPLE")
endif()

if(COMMAND ps2x_stage_ffmpeg_runtime_dlls)
    ps2x_stage_ffmpeg_runtime_dlls(ps2_host_runtime)
endif()

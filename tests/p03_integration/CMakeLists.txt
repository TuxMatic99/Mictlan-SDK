cmake_minimum_required(VERSION 3.26)
project(MictlanP033Integration LANGUAGES C)
enable_testing()
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(NOT EXISTS "${LATINO_INCLUDE_DIR}/latino.h" OR NOT EXISTS "${LATINO_LIBRARY}")
    message(FATAL_ERROR "Indicar cabeceras y liblatino.so del mismo Core")
endif()
get_filename_component(CORE_ROOT "${LATINO_INCLUDE_DIR}/.." ABSOLUTE)
get_filename_component(SDK_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
add_executable(p033_integracion contratos.c
    "${SDK_ROOT}/src/ciencia/mictlan_ciencia_ffi.c"
    "${SDK_ROOT}/src/ciencia/vectores2d.c")
target_include_directories(p033_integracion PRIVATE "${LATINO_INCLUDE_DIR}"
    "${CORE_ROOT}/src" "${SDK_ROOT}/include")
target_link_libraries(p033_integracion PRIVATE "${LATINO_LIBRARY}" m)
target_compile_options(p033_integracion PRIVATE -Wall -Wextra -Wpedantic)
foreach(caso IN ITEMS identidad repetidos reemplazo alias_ffi)
    add_test(NAME p033_${caso} COMMAND p033_integracion ${caso})
    set_tests_properties(p033_${caso} PROPERTIES TIMEOUT 60 LABELS "p033;integracion"
        FAIL_REGULAR_EXPRESSION "AddressSanitizer;UndefinedBehaviorSanitizer;LeakSanitizer;runtime error:;P033_ASSERT")
endforeach()
# Las fugas del uso normal FFI siguen siendo fallos, nunca WILL_FAIL ni skip.
set_tests_properties(p033_alias_ffi PROPERTIES LABELS "p033;integracion;memoria_pendiente")

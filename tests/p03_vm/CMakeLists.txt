cmake_minimum_required(VERSION 3.18)
project(MictlanP03VM LANGUAGES C)
include(CTest)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
if(NOT EXISTS "${LATINO_INCLUDE_DIR}/latino.h" OR NOT EXISTS "${LATINO_LIBRARY}")
    message(FATAL_ERROR "Indicar LATINO_INCLUDE_DIR y LATINO_LIBRARY del mismo Core")
endif()
get_filename_component(SDK_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
add_executable(p03_vm_recuperacion
    recuperacion_vm.c
    "${SDK_ROOT}/src/ciencia/mictlan_ciencia_ffi.c"
    "${SDK_ROOT}/src/ciencia/vectores2d.c")
target_include_directories(p03_vm_recuperacion PRIVATE
    "${LATINO_INCLUDE_DIR}" "${SDK_ROOT}/include")
target_link_libraries(p03_vm_recuperacion PRIVATE "${LATINO_LIBRARY}" m)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(p03_vm_recuperacion PRIVATE -Wall -Wextra -Wpedantic)
endif()
foreach(mode IN ITEMS control directa anidada pila)
    add_test(NAME p03_vm_${mode}_200 COMMAND p03_vm_recuperacion ${mode} 200)
    set_tests_properties(p03_vm_${mode}_200 PROPERTIES
        TIMEOUT 60 LABELS "p03;vm;${mode}"
        FAIL_REGULAR_EXPRESSION "AddressSanitizer;UndefinedBehaviorSanitizer;LeakSanitizer;runtime error:")
endforeach()
# No WILL_FAIL ni SKIP_RETURN_CODE: un defecto conocido sigue siendo un fallo.
set_tests_properties(p03_vm_directa_200 p03_vm_anidada_200 PROPERTIES
    LABELS "p03;vm;recuperacion")
set_tests_properties(p03_vm_pila_200 PROPERTIES
    LABELS "p03;vm;fallo_conocido")

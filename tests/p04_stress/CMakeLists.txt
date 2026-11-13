cmake_minimum_required(VERSION 3.26)
project(MictlanP04Stress LANGUAGES C)
get_filename_component(SDK_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
if(NOT EXISTS "${LATINO_INCLUDE_DIR}/latino.h" OR NOT EXISTS "${LATINO_LIBRARY}" OR
   NOT EXISTS "${P04_MEMORY_HEADER}/latmemoria.h")
  message(FATAL_ERROR "Indicar Core y el directorio de la API experimental")
endif()
add_executable(p04_carga carga.c "${SDK_ROOT}/src/ciencia/mictlan_ciencia_ffi.c"
  "${SDK_ROOT}/src/ciencia/vectores2d.c")
set_target_properties(p04_carga PROPERTIES C_STANDARD 11 C_STANDARD_REQUIRED YES)
target_include_directories(p04_carga PRIVATE "${LATINO_INCLUDE_DIR}" "${P04_MEMORY_HEADER}"
  "${SDK_ROOT}/include")
target_link_libraries(p04_carga PRIVATE "${LATINO_LIBRARY}" ${CMAKE_DL_LIBS} m)
target_compile_options(p04_carga PRIVATE -Wall -Wextra -Wpedantic)

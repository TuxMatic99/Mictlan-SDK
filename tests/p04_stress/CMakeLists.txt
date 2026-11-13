cmake_minimum_required(VERSION 3.26)
project(MictlanP04Stress LANGUAGES C)
get_filename_component(SDK_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
if(NOT EXISTS "${LATINO_INCLUDE_DIR}/latino.h" OR NOT EXISTS "${LATINO_LIBRARY}" OR
   NOT EXISTS "${P04_MEMORY_HEADER}/latmemoria.h" OR
   NOT EXISTS "${P04_BASE_INCLUDE}/latino.h" OR NOT EXISTS "${P04_BASE_LIBRARY}")
  message(FATAL_ERROR "Indicar Core, Core base y el directorio de la API experimental")
endif()
set(SCIENCE_SOURCES "${SDK_ROOT}/src/ciencia/mictlan_ciencia_ffi.c"
  "${SDK_ROOT}/src/ciencia/vectores2d.c")
add_executable(p04_carga carga.c ${SCIENCE_SOURCES})
set_target_properties(p04_carga PROPERTIES C_STANDARD 11 C_STANDARD_REQUIRED YES)
target_include_directories(p04_carga PRIVATE "${LATINO_INCLUDE_DIR}" "${P04_MEMORY_HEADER}"
  "${SDK_ROOT}/include")
target_link_libraries(p04_carga PRIVATE "${LATINO_LIBRARY}" ${CMAKE_DL_LIBS} m)
target_compile_options(p04_carga PRIVATE -Wall -Wextra -Wpedantic)

# Reusar el consumidor real del SDK, compilado con las cabeceras y el
# enlazador de F+E. La batería lo ejecuta sin recompilar con ambas bibliotecas.
add_executable(p04_sdk_anterior "${SDK_ROOT}/src/ciencia/mictlan_ciencia_consola.c"
  ${SCIENCE_SOURCES})
set_target_properties(p04_sdk_anterior PROPERTIES C_STANDARD 11 C_STANDARD_REQUIRED YES)
target_include_directories(p04_sdk_anterior PRIVATE "${P04_BASE_INCLUDE}" "${SDK_ROOT}/include")
target_link_libraries(p04_sdk_anterior PRIVATE "${P04_BASE_LIBRARY}" m)

cmake_minimum_required(VERSION 3.18)

project(LatinoVox
    VERSION 0.1.0
    LANGUAGES C
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 1. Buscar Raylib en el sistema
find_package(raylib CONFIG REQUIRED)

# 2. Detectar un conjunto completo y coherente de cabeceras Latino-Core.
# Si el usuario proporciona -DLATINO_INCLUDE_DIR, respetar esa selección,
# pero comprobar que no falten las dependencias incluidas por latino.h.
set(_LATINO_HEADERS latino.h latclass.h latast.h latmv.h latobj.h)
set(_LATINO_CANDIDATES
    "${LATINO_INCLUDE_DIR}"
    "$ENV{HOME}/latino-core/include"
    "/usr/local/include"
    "/usr/include"
)
set(_LATINO_HEADERS_FOUND FALSE)
foreach(_candidate IN LISTS _LATINO_CANDIDATES)
    if(NOT IS_DIRECTORY "${_candidate}")
        continue()
    endif()
    set(_complete TRUE)
    foreach(_header IN LISTS _LATINO_HEADERS)
        if(NOT EXISTS "${_candidate}/${_header}")
            set(_complete FALSE)
            break()
        endif()
    endforeach()
    if(_complete)
        set(LATINO_INCLUDE_DIR "${_candidate}" CACHE PATH
            "Directorio con cabeceras completas de Latino-Core" FORCE)
        set(_LATINO_HEADERS_FOUND TRUE)
        break()
    endif()
endforeach()
if(NOT _LATINO_HEADERS_FOUND)
    message(FATAL_ERROR
        "No se encontraron las cabeceras completas de Latino-Core. "
        "Configura -DLATINO_INCLUDE_DIR=/ruta/latino-core/include")
endif()
message(STATUS "Latino-Core headers: ${LATINO_INCLUDE_DIR}")

find_library(LATINO_LIBRARY
    NAMES latino liblatino
    PATHS /usr/local/lib
    REQUIRED
)

add_executable(motor
    src/main.c
)

target_include_directories(motor
    PRIVATE
    ${LATINO_INCLUDE_DIR}
)

target_link_libraries(motor
    PRIVATE
    raylib
    ${LATINO_LIBRARY}
    m
)

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(motor PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )
endif()

# Motor geométrico independiente
add_library(latino_ui_layout STATIC
    src/ui/ui_layout.c
)

target_include_directories(latino_ui_layout
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(motor
    PRIVATE
        latino_ui_layout
)

# Pruebas automatizadas
include(CTest)

if(BUILD_TESTING)
    add_executable(test_ui_layout
        tests/test_ui_layout.c
    )

    target_link_libraries(test_ui_layout
        PRIVATE
            latino_ui_layout
            m
    )

    add_test(
        NAME latino_ui_layout_basico
        COMMAND test_ui_layout
    )
endif()

# Demostración gráfica del motor de maquetación
add_executable(demo_ui_layout
    tests/demo_ui_layout.c
)

target_link_libraries(demo_ui_layout
    PRIVATE
        latino_ui_layout
        raylib
        m
)

# Biblioteca independiente de contenedores
add_library(latino_ui_contenedores STATIC
    src/ui/ui_contenedores.c
)

target_include_directories(latino_ui_contenedores
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

if(BUILD_TESTING)
    add_executable(test_ui_contenedores
        tests/test_ui_contenedores.c
    )

    target_link_libraries(test_ui_contenedores
        PRIVATE
            latino_ui_contenedores
            m
    )

    add_test(
        NAME latino_ui_contenedores_basico
        COMMAND test_ui_contenedores
    )
endif()
# Agrupación de widgets administrada por el módulo independiente.
target_link_libraries(motor PRIVATE latino_ui_contenedores)


# Pruebas adicionales del ciclo de vida de contenedores
if(BUILD_TESTING)
    add_executable(test_ui_contenedores_estabilidad
        tests/test_ui_contenedores_estabilidad.c
    )

    target_link_libraries(test_ui_contenedores_estabilidad
        PRIVATE
            latino_ui_contenedores
    )

    add_test(
        NAME latino_ui_contenedores_estabilidad
        COMMAND test_ui_contenedores_estabilidad
    )
endif()

# LatinoUI Tree: estructura jerárquica independiente
add_library(latino_ui_arbol STATIC
    src/ui/ui_arbol.c
)

target_include_directories(latino_ui_arbol
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

if(BUILD_TESTING)
    add_executable(test_ui_arbol
        tests/test_ui_arbol.c
    )

    target_link_libraries(test_ui_arbol
        PRIVATE
            latino_ui_arbol
    )

    add_test(
        NAME latino_ui_arbol_basico
        COMMAND test_ui_arbol
    )
endif()

# Pruebas de estabilidad de LatinoUI Tree
if(BUILD_TESTING)
    add_executable(test_ui_arbol_estabilidad
        tests/test_ui_arbol_estabilidad.c
    )

    target_link_libraries(test_ui_arbol_estabilidad
        PRIVATE latino_ui_arbol
    )

    add_test(
        NAME latino_ui_arbol_estabilidad
        COMMAND test_ui_arbol_estabilidad
    )
endif()

# LatinoUI: motor de geometría jerárquica
add_library(latino_ui_layout_arbol STATIC
    src/ui/ui_layout_arbol.c
)

target_include_directories(latino_ui_layout_arbol
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(latino_ui_layout_arbol
    PUBLIC
        latino_ui_arbol
        latino_ui_layout
)

if(BUILD_TESTING)
    add_executable(test_ui_layout_arbol
        tests/test_ui_layout_arbol.c
    )

    target_link_libraries(test_ui_layout_arbol
        PRIVATE
            latino_ui_layout_arbol
            m
    )

    add_test(
        NAME latino_ui_layout_arbol_basico
        COMMAND test_ui_layout_arbol
    )
endif()

# Demostración visual independiente de LatinoUI Tree
add_executable(demo_ui_layout_arbol
    tests/demo_ui_layout_arbol.c
)

target_link_libraries(demo_ui_layout_arbol
    PRIVATE
        latino_ui_layout_arbol
        raylib
        m
)


# Primera aplicación autónoma de LatinoUI
add_executable(host_ui
    src/ui/host_ui.c
)

if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set_target_properties(host_ui PROPERTIES INSTALL_RPATH "$ORIGIN/../lib")
    install(TARGETS host_ui RUNTIME DESTINATION bin COMPONENT MictlanAplicaciones
            EXCLUDE_FROM_ALL)
endif()

target_include_directories(host_ui
    PRIVATE
        ${LATINO_INCLUDE_DIR}
)

target_link_libraries(host_ui
    PRIVATE
        raylib
        ${LATINO_LIBRARY}
        m
)

# El motor reutiliza el mismo UTF-8 estricto, sin depender del catálogo.
target_sources(motor PRIVATE src/ui/ui_utf8.c)

# LatinoUI Runtime: administracion independiente de widgets
add_library(latino_ui_runtime STATIC
    src/ui/ui_runtime.c
    src/ui/ui_utf8.c
)

target_include_directories(latino_ui_runtime
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(latino_ui_runtime
    PUBLIC
        latino_ui_layout_arbol
)

target_link_libraries(host_ui
    PRIVATE
        latino_ui_runtime
)

if(BUILD_TESTING)
    add_executable(test_ui_runtime
        tests/test_ui_runtime.c
    )

    target_link_libraries(test_ui_runtime
        PRIVATE
            latino_ui_runtime
            m
    )

    add_test(
        NAME latino_ui_runtime_basico
        COMMAND test_ui_runtime
    )
endif()

# LatinoUI: sistema independiente de eventos
add_library(latino_ui_eventos STATIC
    src/ui/ui_eventos.c
)

target_include_directories(latino_ui_eventos
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

if(BUILD_TESTING)
    add_executable(test_ui_eventos
        tests/test_ui_eventos.c
    )

    target_link_libraries(test_ui_eventos
        PRIVATE
            latino_ui_eventos
    )

    add_test(
        NAME latino_ui_eventos_basico
        COMMAND test_ui_eventos
    )
endif()

# Integracion de eventos con el host autonomo
target_link_libraries(host_ui
    PRIVATE
        latino_ui_eventos
)

add_library(latino_ui_callbacks STATIC src/ui/ui_callbacks.c)
target_include_directories(latino_ui_callbacks PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${LATINO_INCLUDE_DIR}
)
target_link_libraries(latino_ui_callbacks PUBLIC ${LATINO_LIBRARY})

if(BUILD_TESTING)
    add_executable(test_ui_callbacks tests/test_ui_callbacks.c)
    target_include_directories(test_ui_callbacks PRIVATE ${LATINO_INCLUDE_DIR})
    target_link_libraries(test_ui_callbacks PRIVATE latino_ui_callbacks m)
    add_test(NAME latino_ui_callbacks_trampolin
        COMMAND test_ui_callbacks
            "${CMAKE_CURRENT_SOURCE_DIR}/scripts/prueba_callbacks.lat")
endif()

# LatinoUI despachador independiente v0.1
add_library(latino_ui_despachador STATIC src/ui/ui_despachador.c)
target_include_directories(latino_ui_despachador PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(latino_ui_despachador PUBLIC latino_ui_eventos)

if(BUILD_TESTING)
    add_executable(test_ui_integracion_fifo tests/test_ui_integracion_fifo.c)
    target_link_libraries(test_ui_integracion_fifo PRIVATE latino_ui_despachador)
    add_test(NAME latino_ui_integracion_fifo COMMAND test_ui_integracion_fifo)
    set_tests_properties(latino_ui_integracion_fifo PROPERTIES TIMEOUT 10)

    add_executable(test_ui_despachador_error tests/test_ui_despachador_error.c)
    target_link_libraries(test_ui_despachador_error PRIVATE latino_ui_despachador)
    add_test(NAME latino_ui_despachador_error COMMAND test_ui_despachador_error)
    set_tests_properties(latino_ui_despachador_error PROPERTIES TIMEOUT 10)
endif()

# Integracion real del host con FIFO, despachador y callbacks Latino
target_link_libraries(host_ui PRIVATE
    latino_ui_despachador
    latino_ui_callbacks
)

include(cmake/LatinoUICatalogo.cmake)
include(cmake/LatinoUIHostTests.cmake)
if(TARGET test_ui_host)
    target_link_libraries(test_ui_host PRIVATE latino_ui_biblioteca)
endif()

# Las pruebas previas usan assert: Release tambien debe ejecutar sus comprobaciones.
if(BUILD_TESTING)
    get_property(_ui_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
    foreach(_ui_target IN LISTS _ui_targets)
        if(_ui_target MATCHES "^test_")
            if(MSVC)
                target_compile_options(${_ui_target} PRIVATE /UNDEBUG)
            elseif(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
                target_compile_options(${_ui_target} PRIVATE -UNDEBUG)
            endif()
        endif()
    endforeach()
endif()



# Mictlan: comandos de dibujo 2D
add_library(mictlan_dibujo2d STATIC
    src/graficos/dibujo2d.c
)

target_include_directories(mictlan_dibujo2d
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

if(BUILD_TESTING)
    add_executable(test_mictlan_dibujo2d
        tests/test_mictlan_dibujo2d.c
    )

    target_link_libraries(test_mictlan_dibujo2d
        PRIVATE mictlan_dibujo2d
    )

    add_test(
        NAME mictlan_dibujo2d_basico
        COMMAND test_mictlan_dibujo2d
    )
endif()



# Backend de renderizado 2D con Raylib

add_library(mictlan_render_raylib STATIC
    src/graficos/dibujo2d_raylib.c
)

target_include_directories(mictlan_render_raylib
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(mictlan_render_raylib
    PUBLIC
        mictlan_dibujo2d
    PRIVATE
        raylib
        m
)



# Demostración visual del renderizador Mictlán 2D

add_executable(demo_mictlan_dibujo2d
    tests/demo_mictlan_dibujo2d.c
)

target_link_libraries(demo_mictlan_dibujo2d
    PRIVATE
        mictlan_render_raylib
        raylib
)



# Integración de gráficos 2D con el host real
target_link_libraries(host_ui
    PRIVATE mictlan_render_raylib
)

# Las pruebas usan almacenamiento real de figuras,
# pero no necesitan un backend de GPU.
if(BUILD_TESTING)
    target_compile_definitions(
        host_ui_para_pruebas
        PRIVATE MICTLAN_HOST_PRUEBAS
    )

    target_link_libraries(
        host_ui_para_pruebas
        PRIVATE mictlan_dibujo2d
    )

    target_link_libraries(
        test_ui_host
        PRIVATE mictlan_dibujo2d
    )
endif()



# Mictlán Graphics:
# Compatibilidad con las pruebas históricas del host.

if(BUILD_TESTING)

    # Prueba de integración de la biblioteca.
    if(TARGET test_ui_biblioteca)

        target_compile_definitions(
            test_ui_biblioteca
            PRIVATE MICTLAN_HOST_PRUEBAS
        )

        target_link_libraries(
            test_ui_biblioteca
            PRIVATE mictlan_dibujo2d
        )

    endif()

    # Prueba del editor y su host.
    if(TARGET test_ui_edicion_host)

        target_compile_definitions(
            test_ui_edicion_host
            PRIVATE MICTLAN_HOST_PRUEBAS
        )

        target_link_libraries(
            test_ui_edicion_host
            PRIVATE mictlan_dibujo2d
        )

    endif()

endif()


# Prueba de integración de la FFI gráfica de Mictlán

if(BUILD_TESTING AND TARGET test_ui_host)

    add_test(
        NAME mictlan_graficos_ffi
        COMMAND test_ui_host
            --graficos
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/datos/mictlan_graficos_ffi.lat"
    )

    set_tests_properties(
        mictlan_graficos_ffi
        PROPERTIES
            PASS_REGULAR_EXPRESSION "FFI_GRAFICOS_OK"
            FAIL_REGULAR_EXPRESSION "FFI_GRAFICOS_FALLO"
            TIMEOUT 10
    )

endif()


# Mictlan Graphics: puente FFI independiente.

add_library(mictlan_graficos_ffi STATIC
    src/graficos/mictlan_graficos_ffi.c
)

target_include_directories(mictlan_graficos_ffi
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${LATINO_INCLUDE_DIR}
)

target_link_libraries(mictlan_graficos_ffi
    PUBLIC mictlan_dibujo2d
    PRIVATE ${LATINO_LIBRARY}
)

# Aplicacion grafica real.
target_link_libraries(host_ui
    PRIVATE mictlan_graficos_ffi
)

# Ejecutables que utilizan el host durante las pruebas.
if(BUILD_TESTING)
    foreach(prueba IN ITEMS
        host_ui_para_pruebas
        test_ui_host
        test_ui_biblioteca
        test_ui_edicion_host
    )
        if(TARGET ${prueba})
            target_link_libraries(${prueba}
                PRIVATE mictlan_graficos_ffi
            )
        endif()
    endforeach()
endif()



# ==============================================
# MICTLAN CIENCIA: VECTORES BIDIMENSIONALES
# ==============================================

# Biblioteca matematica independiente.
add_library(mictlan_ciencia_vectores2d STATIC
    src/ciencia/vectores2d.c
)

# Permitir que otros modulos encuentren su cabecera.
target_include_directories(mictlan_ciencia_vectores2d PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

# En sistemas Unix, enlazar la biblioteca matematica.
if(UNIX)
    target_link_libraries(mictlan_ciencia_vectores2d PUBLIC m)
endif()

# Crear las pruebas solo cuando esten habilitadas.
if(BUILD_TESTING)

    add_executable(test_mictlan_vectores2d
        tests/test_mictlan_vectores2d.c
    )

    target_link_libraries(test_mictlan_vectores2d PRIVATE
        mictlan_ciencia_vectores2d
    )

    add_test(
        NAME mictlan_ciencia_vectores2d_basico
        COMMAND test_mictlan_vectores2d
    )

endif()


# ==============================================
# MICTLAN CIENCIA: PUENTE FFI
# ==============================================

add_library(mictlan_ciencia_ffi STATIC
    src/ciencia/mictlan_ciencia_ffi.c
)

target_include_directories(mictlan_ciencia_ffi
    PUBLIC
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
        "${LATINO_INCLUDE_DIR}"
)

target_link_libraries(mictlan_ciencia_ffi
    PUBLIC mictlan_ciencia_vectores2d
    PRIVATE "${LATINO_LIBRARY}"
)

target_link_libraries(host_ui PRIVATE mictlan_ciencia_ffi)
if(BUILD_TESTING)
    foreach(prueba IN ITEMS host_ui_para_pruebas test_ui_host test_ui_biblioteca test_ui_edicion_host)
        target_link_libraries(${prueba} PRIVATE mictlan_ciencia_ffi)
    endforeach()
endif()

if(BUILD_TESTING)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    foreach(caso IN ITEMS eventos error)
        set(script "${CMAKE_CURRENT_SOURCE_DIR}/tests/p1/${caso}.mict")
        if(caso STREQUAL "error")
            set(script "${CMAKE_CURRENT_SOURCE_DIR}/tests/p1/error_callback.mict")
        endif()
        add_test(NAME mictlan_p1_ui_${caso}
            COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/p1/ejecutar_host.py"
                "$<TARGET_FILE:test_ui_host>" "${caso}" "${script}")
        set_tests_properties(mictlan_p1_ui_${caso} PROPERTIES TIMEOUT 45 LABELS "p1;ui")
    endforeach()
endif()


# ==============================================
# MICTLAN CIENCIA: EJECUTOR DE CONSOLA
# ==============================================

add_executable(mictlan_ciencia_consola
    src/ciencia/mictlan_ciencia_consola.c
)

if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set_target_properties(mictlan_ciencia_consola PROPERTIES INSTALL_RPATH "$ORIGIN/../lib")
    install(TARGETS mictlan_ciencia_consola RUNTIME DESTINATION bin COMPONENT MictlanAplicaciones
            EXCLUDE_FROM_ALL)
endif()

target_link_libraries(mictlan_ciencia_consola
    PRIVATE
        mictlan_ciencia_ffi
        "${LATINO_LIBRARY}"
        m
)



# ==============================================
# MICTLAN CIENCIA: PRUEBA DE INTEGRACION
# ==============================================

if(BUILD_TESTING)

    add_test(
        NAME mictlan_ciencia_longitud_integracion
        COMMAND
            "${CMAKE_COMMAND}"
            "-DMICTLAN_EJECUTABLE=$<TARGET_FILE:mictlan_ciencia_consola>"
            "-DMICTLAN_PROGRAMA=${CMAKE_CURRENT_SOURCE_DIR}/tests/datos/mictlan_ciencia_longitud.mict"
            -P
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/verificar_ciencia.cmake"
    )

    set_tests_properties(
        mictlan_ciencia_longitud_integracion
        PROPERTIES TIMEOUT 15
    )

endif()



# ==============================================
# MICTLAN CIENCIA: PRUEBA DEL PRODUCTO PUNTO
# ==============================================

if(BUILD_TESTING)

    add_test(
        NAME mictlan_ciencia_producto_punto_integracion
        COMMAND
            "${CMAKE_COMMAND}"
            "-DMICTLAN_EJECUTABLE=$<TARGET_FILE:mictlan_ciencia_consola>"
            "-DMICTLAN_PROGRAMA=${CMAKE_CURRENT_SOURCE_DIR}/tests/datos/mictlan_producto_punto.mict"
            -P
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/verificar_producto_punto.cmake"
    )

    set_tests_properties(
        mictlan_ciencia_producto_punto_integracion
        PROPERTIES TIMEOUT 15
    )

endif()


# ==============================================
# MICTLAN CIENCIA: PRUEBA DE SUMA VECTORIAL
# ==============================================

if(BUILD_TESTING)

    add_test(
        NAME mictlan_ciencia_suma_vectorial_integracion
        COMMAND
            "${CMAKE_COMMAND}"
            "-DMICTLAN_EJECUTABLE=$<TARGET_FILE:mictlan_ciencia_consola>"
            "-DMICTLAN_PROGRAMA=${CMAKE_CURRENT_SOURCE_DIR}/tests/datos/mictlan_suma_vectorial.mict"
            -P
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/verificar_suma_vectorial.cmake"
    )

    set_tests_properties(
        mictlan_ciencia_suma_vectorial_integracion
        PROPERTIES TIMEOUT 15
    )

endif()



# ==============================================
# MICTLAN CIENCIA: ERROR DE TIPO EN SUMA
# ==============================================

if(BUILD_TESTING)

    add_test(
        NAME mictlan_ciencia_suma_error_tipo
        COMMAND
            "${CMAKE_COMMAND}"
            "-DMICTLAN_EJECUTABLE=$<TARGET_FILE:mictlan_ciencia_consola>"
            "-DMICTLAN_PROGRAMA=${CMAKE_CURRENT_SOURCE_DIR}/tests/datos/mictlan_suma_error_tipo.mict"
            -P
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/verificar_suma_error_tipo.cmake"
    )

    set_tests_properties(
        mictlan_ciencia_suma_error_tipo
        PROPERTIES TIMEOUT 15
    )

endif()


# ==============================================
# MICTLAN CIENCIA: DESBORDAMIENTO EN SUMA
# ==============================================

if(BUILD_TESTING)

    add_test(
        NAME mictlan_ciencia_suma_error_rango
        COMMAND
            "${CMAKE_COMMAND}"
            "-DMICTLAN_EJECUTABLE=$<TARGET_FILE:mictlan_ciencia_consola>"
            "-DMICTLAN_PROGRAMA=${CMAKE_CURRENT_SOURCE_DIR}/tests/datos/mictlan_suma_error_rango.mict"
            -P
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/verificar_suma_error_rango.cmake"
    )

    set_tests_properties(
        mictlan_ciencia_suma_error_rango
        PROPERTIES TIMEOUT 15
    )

endif()


# ==============================================
# MICTLAN CIENCIA: REFERENCIAS COMPARTIDAS FFI
# ==============================================

if(BUILD_TESTING)

    add_test(
        NAME mictlan_ciencia_alias_vector_ffi
        COMMAND
            "${CMAKE_COMMAND}"
            "-DMICTLAN_EJECUTABLE=$<TARGET_FILE:mictlan_ciencia_consola>"
            "-DMICTLAN_PROGRAMA=${CMAKE_CURRENT_SOURCE_DIR}/tests/datos/mictlan_alias_vector_ffi.mict"
            -P
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/verificar_alias_vector_ffi.cmake"
    )

    set_tests_properties(
        mictlan_ciencia_alias_vector_ffi
        PROPERTIES TIMEOUT 15
    )

endif()

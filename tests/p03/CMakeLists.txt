cmake_minimum_required(VERSION 3.18)
project(MictlanP03Verificadores LANGUAGES NONE)
enable_testing()
if(NOT UNIX)
    message(FATAL_ERROR "Esta bateria P0.3-1 utiliza fixtures POSIX; validar otros sistemas por separado")
endif()
find_package(Python3 3.8 REQUIRED COMPONENTS Interpreter)

set(P03_ESCENARIOS
    limpio asan ubsan lsan ubsan_sin_nombre asan_deadlysignal
    asan_stdout ubsan_stdout lsan_stdout lsan_ptrace lsan_fatal
    uaf_y_ptrace salida_cero sin_diagnostico salida_extra timeout senal
    ejecutable_ausente programa_ausente lsan_exitcode_cero asan_sin_fugas
    lsan_sin_cierre ubsan_sin_parada log_externo log_duplicado supresion
    timeout_cero lsan_exitcode_ceros
)
foreach(caso tipo rango)
    foreach(escenario IN LISTS P03_ESCENARIOS)
        add_test(NAME p03_verificador_${caso}_${escenario}
            COMMAND "${Python3_EXECUTABLE}"
                "${CMAKE_CURRENT_LIST_DIR}/probar_verificador.py"
                --cmake "${CMAKE_COMMAND}"
                --caso "${caso}" --escenario "${escenario}")
        set_tests_properties(p03_verificador_${caso}_${escenario} PROPERTIES
            TIMEOUT 20 LABELS "p03;verificadores;simulado")
    endforeach()
endforeach()

foreach(escenario valido limpio_bloqueado fuga_bloqueada detector_silencioso
                  limpio_con_fuga uaf_y_bloqueo fuga_sin_error timeout cantidad_distinta)
    add_test(NAME p03_preflight_${escenario}
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_LIST_DIR}/probar_automatizacion.py" "${escenario}")
    set_tests_properties(p03_preflight_${escenario} PROPERTIES
        TIMEOUT 10 LABELS "p03;preflight;simulado")
endforeach()

include_guard(GLOBAL)

# Todas las salidas se conservan antes de aceptar o rechazar el proceso.
# MICTLAN_LOG_DIR es opcional; cada invocacion concurrente necesita su directorio.
function(p03_finalizar clasificacion detalle)
    if(DEFINED MICTLAN_LOG_DIR AND NOT "${MICTLAN_LOG_DIR}" STREQUAL "")
        file(MAKE_DIRECTORY "${MICTLAN_LOG_DIR}")
        file(WRITE "${MICTLAN_LOG_DIR}/stdout.log" "${salida}")
        file(WRITE "${MICTLAN_LOG_DIR}/stderr.log" "${errores}")
        file(WRITE "${MICTLAN_LOG_DIR}/estado.txt" "${estado}\n")
        file(WRITE "${MICTLAN_LOG_DIR}/clasificacion.txt" "${clasificacion}\n")
    endif()
    if("${clasificacion}" STREQUAL "PASS")
        message(STATUS "MICTLAN_SUMA_ERROR_${caso}_OK")
    else()
        message(FATAL_ERROR
            "P03_${clasificacion}: ${detalle}\n"
            "Estado del proceso: ${estado}\n"
            "--- stdout ---\n${salida}\n--- stderr ---\n${errores}")
    endif()
endfunction()

function(mictlan_verificar_error_esperado caso diagnostico encabezado)
    set(estado "NOT_EXECUTED")
    set(salida "")
    set(errores "")
    foreach(parametro MICTLAN_EJECUTABLE MICTLAN_PROGRAMA)
        if(NOT DEFINED ${parametro} OR "${${parametro}}" STREQUAL "")
            p03_finalizar(INVALID_CONFIG "Falta ${parametro}")
        endif()
        if(NOT EXISTS "${${parametro}}" OR IS_DIRECTORY "${${parametro}}")
            p03_finalizar(INVALID_CONFIG "Archivo inexistente: ${parametro}=${${parametro}}")
        endif()
    endforeach()

    # No permitir que la configuracion oculte diagnosticos al verificador.
    # No se altera el entorno recibido: las opciones adicionales siguen activas.
    foreach(variable ASAN_OPTIONS UBSAN_OPTIONS LSAN_OPTIONS)
        string(TOLOWER "$ENV{${variable}}" opciones)
        if(opciones MATCHES "(^|:)(detect_leaks|leak_check_at_exit|halt_on_error|detect_stack_use_after_return|alloc_dealloc_mismatch)=(0|false)(:|$)"
           OR opciones MATCHES "(^|:)exitcode=[+]?0+(:|$)"
           OR opciones MATCHES "(^|:)start_deactivated=(1|true)(:|$)"
           OR opciones MATCHES "(^|:)suppressions=[^:]+")
            p03_finalizar(INVALID_CONFIG "${variable} desactiva controles o suprime errores")
        endif()
        string(REPLACE ":" ";" opciones_lista "${opciones}")
        foreach(opcion IN LISTS opciones_lista)
            if(opcion MATCHES "^log_path=(.*)$")
                if(NOT CMAKE_MATCH_1 STREQUAL "stderr" AND NOT CMAKE_MATCH_1 STREQUAL "stdout")
                    p03_finalizar(INVALID_CONFIG "${variable} redirige diagnosticos fuera de los streams capturados")
                endif()
            endif()
        endforeach()
    endforeach()

    if(NOT DEFINED MICTLAN_TIMEOUT)
        set(MICTLAN_TIMEOUT 10)
    endif()
    if(NOT "${MICTLAN_TIMEOUT}" MATCHES "^[0-9]+([.][0-9]+)?$"
       OR MICTLAN_TIMEOUT LESS_EQUAL 0 OR MICTLAN_TIMEOUT GREATER 10)
        p03_finalizar(INVALID_CONFIG "MICTLAN_TIMEOUT debe ser mayor que 0 y menor o igual que 10")
    endif()

    execute_process(
        COMMAND "${MICTLAN_EJECUTABLE}" "${MICTLAN_PROGRAMA}"
        RESULT_VARIABLE estado
        OUTPUT_VARIABLE salida
        ERROR_VARIABLE errores
        TIMEOUT "${MICTLAN_TIMEOUT}"
    )

    string(TOLOWER "${salida}\n${errores}" observado)
    # Un defecto real conserva prioridad si coexiste con un bloqueo de LSan.
    if(observado MATCHES "addresssanitizer|undefinedbehaviorsanitizer|runtime error:"
       OR observado MATCHES "leaksanitizer: detected memory leaks")
        p03_finalizar(FAIL_SANITIZER "Informe de ASan, UBSan o LSan")
    endif()
    if(observado MATCHES "leaksanitizer has encountered a fatal error"
       OR observado MATCHES "leaksanitizer does not work under ptrace")
        p03_finalizar(BLOCKED_INFRASTRUCTURE "LeakSanitizer no pudo ejecutar su comprobacion; no es una prueba aprobada")
    endif()
    if(observado MATCHES "sanitizer|(^|[^a-z])(asan|ubsan|lsan):")
        p03_finalizar(FAIL_SANITIZER "Diagnostico adicional de sanitizador")
    endif()
    if("${estado}" MATCHES "[Tt]imeout")
        p03_finalizar(FAIL_TIMEOUT "La prueba excedio su tiempo limite")
    endif()
    if(NOT "${estado}" STREQUAL "1")
        p03_finalizar(FAIL_EXIT "El error del lenguaje debe terminar exactamente con codigo 1")
    endif()
    string(FIND "${errores}" "${diagnostico}" posicion_error)
    if(posicion_error EQUAL -1)
        p03_finalizar(FAIL_DIAGNOSTIC "No aparecio el diagnostico esperado")
    endif()
    string(STRIP "${salida}" salida_normalizada)
    if(NOT "${salida_normalizada}" STREQUAL "${encabezado}")
        p03_finalizar(FAIL_OUTPUT "La salida no coincide con el encabezado esperado")
    endif()
    p03_finalizar(PASS "Error del lenguaje observado sin contaminacion")
endfunction()

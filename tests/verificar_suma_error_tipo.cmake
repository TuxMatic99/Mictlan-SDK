
# Verificar que Mictlan rechaza argumentos incorrectos.

if(NOT DEFINED MICTLAN_EJECUTABLE OR
   NOT DEFINED MICTLAN_PROGRAMA)
    message(FATAL_ERROR "Faltan parametros")
endif()

execute_process(
    COMMAND
        "${MICTLAN_EJECUTABLE}"
        "${MICTLAN_PROGRAMA}"
    RESULT_VARIABLE estado
    OUTPUT_VARIABLE salida
    ERROR_VARIABLE errores
    TIMEOUT 10
)

# El error observado debe producir salida 1.
if(NOT "${estado}" STREQUAL "1")
    message(FATAL_ERROR
        "Codigo de salida inesperado: ${estado}")
endif()

# Comprobar que aparece el diagnostico.
string(FIND
    "${errores}"
    "El parametro debe de ser un decimal"
    posicion_error
)

if(posicion_error EQUAL -1)
    message(FATAL_ERROR
        "No aparecio el error esperado: ${errores}")
endif()

# Comprobar que la ejecucion se detuvo.
string(STRIP "${salida}" salida)

if(NOT "${salida}" STREQUAL
   "=== PRUEBA DE ERROR DE TIPO ===")
    message(FATAL_ERROR
        "Salida inesperada: ${salida}")
endif()

message(STATUS "MICTLAN_SUMA_ERROR_TIPO_OK")

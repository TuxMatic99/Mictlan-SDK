
# Verificar el rechazo de un desbordamiento numerico.

if(NOT DEFINED MICTLAN_EJECUTABLE OR
   NOT DEFINED MICTLAN_PROGRAMA)
    message(FATAL_ERROR "Faltan parametros de prueba")
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

# El ejecutor debe rechazar la operacion.
if(NOT "${estado}" STREQUAL "1")
    message(FATAL_ERROR
        "Codigo de salida inesperado: ${estado}")
endif()

# Debe indicar especificamente un resultado fuera de rango.
string(FIND
    "${errores}"
    "ciencia.sumar2: resultado fuera de rango"
    posicion_error
)

if(posicion_error EQUAL -1)
    message(FATAL_ERROR
        "No aparecio el diagnostico esperado: ${errores}")
endif()

# Solo debe imprimirse el encabezado anterior al error.
string(STRIP "${salida}" salida)

if(NOT "${salida}" STREQUAL
   "=== PRUEBA DE DESBORDAMIENTO ===")
    message(FATAL_ERROR
        "El programa produjo una salida inesperada: ${salida}")
endif()

message(STATUS "MICTLAN_SUMA_ERROR_RANGO_OK")

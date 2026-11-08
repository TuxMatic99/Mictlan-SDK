
# Verificacion del primer experimento cientifico
# de Mictlan.

if(NOT DEFINED MICTLAN_EJECUTABLE OR
   NOT DEFINED MICTLAN_PROGRAMA)
    message(FATAL_ERROR
        "Faltan los parametros de la prueba")
endif()

execute_process(
    COMMAND
        "${MICTLAN_EJECUTABLE}"
        "${MICTLAN_PROGRAMA}"
    RESULT_VARIABLE resultado
    OUTPUT_VARIABLE salida
    ERROR_VARIABLE errores
    TIMEOUT 10
)

# El interprete debe terminar correctamente.
if(NOT "${resultado}" STREQUAL "0")
    message(FATAL_ERROR
        "Fallo el interprete: ${resultado}\n${errores}")
endif()

# Normalizar los saltos de linea y espacios finales.
string(REPLACE "\r\n" "\n" salida "${salida}")
string(STRIP "${salida}" salida)

# Comprobar exactamente el resultado esperado.
if(NOT salida STREQUAL "Longitud del vector:\n5")
    message(FATAL_ERROR
        "Resultado cientifico inesperado:\n${salida}")
endif()

message(STATUS "MICTLAN_CIENCIA_OK: longitud=5")

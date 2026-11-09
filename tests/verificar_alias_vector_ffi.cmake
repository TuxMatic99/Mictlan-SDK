
# Regresion: referencias compartidas de vectores FFI.

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

if(NOT "${estado}" STREQUAL "0")
    message(FATAL_ERROR
        "Ejecucion fallida: ${estado}\n${errores}")
endif()

string(REPLACE "\r\n" "\n" salida "${salida}")
string(STRIP "${salida}" salida)

string(JOIN "\n" esperado
    "=== ALIAS VECTOR FFI ==="
    "Valor desde original:"
    "99"
    "Valor conservado por alias:"
    "99"
    "Valor de la nueva lista:"
    "7"
    "Segundo componente del alias:"
    "77"
    "=== FIN ==="
)

if(NOT "${salida}" STREQUAL "${esperado}")
    message(FATAL_ERROR
        "Salida inesperada.\nEsperada:\n${esperado}\nObtenida:\n${salida}")
endif()

message(STATUS "MICTLAN_ALIAS_VECTOR_FFI_OK")

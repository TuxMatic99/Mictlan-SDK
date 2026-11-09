
# Verificar automaticamente la suma vectorial de Mictlan.

if(NOT DEFINED MICTLAN_EJECUTABLE OR
   NOT DEFINED MICTLAN_PROGRAMA)
    message(FATAL_ERROR "Faltan parametros de prueba")
endif()

# Ejecutar el programa escrito en Mictlan.
execute_process(
    COMMAND
        "${MICTLAN_EJECUTABLE}"
        "${MICTLAN_PROGRAMA}"
    RESULT_VARIABLE estado
    OUTPUT_VARIABLE salida
    ERROR_VARIABLE errores
    TIMEOUT 10
)

# Comprobar que termino correctamente.
if(NOT "${estado}" STREQUAL "0")
    message(FATAL_ERROR
        "Fallo la ejecucion: ${estado}\n${errores}")
endif()

# Normalizar los saltos de linea.
string(REPLACE "\r\n" "\n" salida "${salida}")
string(STRIP "${salida}" salida)


# Salida matematica esperada.
set(esperado
"=== SUMA VECTORIAL ===
Componente X:
8
Componente Y:
16
=== SUMA DE CEROS ===
0
0
=== SIGNOS MIXTOS ===
2
-8
=== FIN ==="
)


# Comparar el resultado completo.
if(NOT "${salida}" STREQUAL "${esperado}")
    message(FATAL_ERROR
        "Resultado incorrecto:\n${salida}")
endif()

message(STATUS "MICTLAN_SUMA_VECTORIAL_OK")


# Prueba automatica del producto punto de Mictlan.

if(NOT DEFINED MICTLAN_EJECUTABLE OR
   NOT DEFINED MICTLAN_PROGRAMA)
    message(FATAL_ERROR "Faltan parametros de prueba")
endif()

# Ejecutar el programa Mictlan.
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

# Resultado matematico esperado.
set(esperado
"=== PRODUCTO PUNTO ===
Producto punto de (3,4) y (5,12):
63
Producto punto de vectores perpendiculares:
0
=== FIN ==="
)

# Comprobar toda la salida.
if(NOT "${salida}" STREQUAL "${esperado}")
    message(FATAL_ERROR
        "Resultado incorrecto:\n${salida}")
endif()

message(STATUS "MICTLAN_PRODUCTO_PUNTO_OK")

# Un error del lenguaje solo es valido si no hay informes de sanitizadores.
include("${CMAKE_CURRENT_LIST_DIR}/p03/verificar_error_esperado.cmake")
mictlan_verificar_error_esperado(
    TIPO
    "El parametro debe de ser un decimal"
    "=== PRUEBA DE ERROR DE TIPO ==="
)

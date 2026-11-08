
#include "latino.h"
#include "latast.h"
#include "mictlan_ciencia_ffi.h"

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr,
                "Uso: mictlan_ciencia_consola archivo.mict\n");
        return EXIT_FAILURE;
    }

    /* Crear una maquina virtual. */
    lat_mv *mv = latC_crear_mv();

    if (mv == NULL) {
        fprintf(stderr,
                "Error: no se pudo crear la VM.\n");
        return EXIT_FAILURE;
    }

    /* Preparar el contexto del programa. */
    mv->nombre_archivo = argv[1];
    mv->global->REPL = false;

    /* Registrar nuestra biblioteca cientifica. */
    mictlan_ciencia_ffi_registrar(mv);

    /* Analizar el archivo Mictlan. */
    int estado = EXIT_FAILURE;

    ast *nodo = latA_analizar_arch(
        argv[1], &estado
    );

    int codigo_salida = EXIT_FAILURE;

    if (estado == 0 && nodo != NULL) {
        /* Convertir el programa en una funcion. */
        lat_objeto *programa = latC_analizar(mv, nodo);

        if (programa != NULL) {
            /* Ejecutar el programa. */
            estado = latC_llamar_funcion(mv, programa);

            if (estado == 0) {
                codigo_salida = EXIT_SUCCESS;
            }

            latO_destruir(mv, programa);
        }
    }

    if (nodo != NULL) {
        latA_destruir(nodo);
    }

    /* Liberar la maquina virtual. */
    latC_destruir_mv(mv);

    return codigo_salida;
}

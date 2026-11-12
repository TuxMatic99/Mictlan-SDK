#include "latino.h"
#include <stddef.h>
#include <stdio.h>

int main(void)
{
    printf("{\"pointer_size\":%zu,\"lat_objeto_size\":%zu,\"lat_mv_size\":%zu,"
           "\"LAT_ERRRUN\":%d,\"offsets\":{\"ptrctx\":%zu,\"ptrpila\":%zu,"
           "\"numejec\":%zu,\"contexto_actual\":%zu,\"error\":%zu,"
           "\"funciones_propias\":%zu,\"modulos_propios\":%zu,\"constantes_propias\":%zu}}\n",
           sizeof(void *), sizeof(lat_objeto), sizeof(lat_mv), LAT_ERRRUN,
           offsetof(lat_mv, ptrctx), offsetof(lat_mv, ptrpila), offsetof(lat_mv, numejec),
           offsetof(lat_mv, contexto_actual), offsetof(lat_mv, error),
           offsetof(lat_mv, funciones_propias), offsetof(lat_mv, modulos_propios),
           offsetof(lat_mv, constantes_propias));
    return 0;
}

/* Fallos INTENCIONADOS, solo para acreditar detectores en el preflight.
   Nunca enlazado con Core ni incluido en las pruebas funcionales. */
#include <limits.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    if (argc != 2) return 3;
    if (!strcmp(argv[1], "asan")) {
        volatile char *p = malloc(1);
        if (!p) return 3;
        p[1] = 42; /* Debe detenerse con heap-buffer-overflow. */
        free((void *)p);
    } else if (!strcmp(argv[1], "ubsan")) {
        volatile int maximum = INT_MAX;
        volatile int overflow = maximum + 1;
        (void)overflow;
    } else return 3;
    return 0; /* Llegar aqui significa detector silencioso: el verificador falla. */
}

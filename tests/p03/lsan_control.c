/* Control independiente de infraestructura. No enlaza ni modifica Core.
 * Sin argumentos: reserva y libera. Con un argumento: fuga intencional.
 * Un resultado valido requiere control limpio sin errores y deteccion de fuga.
 */
#include <stdlib.h>

__attribute__((noinline)) static void provocar_fuga(void) {
    char *p = malloc(137);
    if (p == NULL) exit(3);
    p[0] = 42;
    __asm__ volatile("" : : "r"(p) : "memory");
}

int main(int argc, char **argv) {
    (void)argv;
    if (argc > 1) {
        provocar_fuga();
    } else {
        void *p = malloc(137);
        if (p == NULL) return 3;
        free(p);
    }
    return 0;
}

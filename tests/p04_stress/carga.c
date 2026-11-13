#define _POSIX_C_SOURCE 200809L
#include "latino.h"
#include "latast.h"
#include "latobj.h"
#include "latmem.h"
#include "latmemoria.h"
#include "mictlan_ciencia_ffi.h"
#include <dlfcn.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>

#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "P04_ASSERT linea %d: %s\n", __LINE__, #x); exit(1); \
} } while (0)

/* Un mismo ELF se ejecuta con ambos Core mediante el cargador. */
typedef struct {
    latG_estado (*habilitar)(lat_mv *);
    latG_estado (*autorizar)(lat_mv *, lat_CFuncion);
    latG_estado (*retener)(lat_mv *, const void *);
    latG_estado (*soltar)(lat_mv *, const void *);
    latG_estado (*recolectar)(lat_mv *);
    latG_estado (*medir)(lat_mv *, latG_medicion *);
} memoria_api;

static memoria_api cargar_api(void) {
    memoria_api api = {0};
#define CARGAR(campo) do { \
    void *p = dlsym(RTLD_DEFAULT, "latG_" #campo); \
    _Static_assert(sizeof(api.campo) == sizeof(p), "ABI Linux de dlsym"); \
    memcpy(&api.campo, &p, sizeof(p)); \
} while (0)
    CARGAR(habilitar);
    CARGAR(autorizar);
    CARGAR(retener);
    CARGAR(soltar);
    CARGAR(recolectar);
    CARGAR(medir);
#undef CARGAR
    return api;
}

typedef struct { ast *arbol; lat_objeto *funcion; } programa;

static programa compilar(lat_mv *mv, const char *fuente) {
    int estado = -1;
    programa p;
    p.arbol = latA_analizar_exp((char *)fuente, &estado);
    CHECK(p.arbol && estado == 0);
    p.funcion = latC_analizar(mv, p.arbol);
    CHECK(p.funcion);
    return p;
}

static lat_objeto *global(lat_mv *mv, const char *nombre) {
    lat_objeto *o = latO_obtener_contexto(mv, mv->contexto[0], nombre);
    CHECK(o);
    return o;
}

static size_t rss_kib(void) {
    FILE *f = fopen("/proc/self/statm", "r");
    size_t paginas = 0, total = 0;
    if (f) {
        if (fscanf(f, "%zu %zu", &total, &paginas) != 2) paginas = 0;
        fclose(f);
    }
    return paginas * (size_t)sysconf(_SC_PAGESIZE) / 1024;
}

static double reloj(void) {
    struct timespec t;
    CHECK(clock_gettime(CLOCK_MONOTONIC, &t) == 0);
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

static void guardar_diccionario(lat_mv *mv, lat_objeto *vector) {
    lat_objeto *sub = latC_crear_lista(mv, latL_crear(mv));
    latL_agregar(mv, getLista(sub), latC_crear_numerico(mv, 7));
    lat_objeto *d = latC_crear_dic(mv, latH_crear(mv));
    latH_asignar(mv, getDic(d), "vector", vector);
    latH_asignar(mv, getDic(d), "sublista", sub);
    latM_liberar(mv, sub);
    latO_asignar_ctx(mv, mv->contexto[0], "contenedor", d);
    latM_liberar(mv, d);
}

static void comprobar(lat_mv *mv, lista *fija) {
    lat_objeto *v = global(mv, "alias");
    lat_objeto *d = global(mv, "contenedor");
    CHECK(v->tipo == T_LIST && d->tipo == T_DIC);
    lat_objeto *copia = latH_obtener(getDic(d), "vector");
    lat_objeto *sub = latH_obtener(getDic(d), "sublista");
    CHECK(copia && copia->tipo == T_LIST && getLista(copia) == getLista(v));
    CHECK(sub && sub->tipo == T_LIST);
    CHECK(getNumerico(latL_obtener_elemento(mv, getLista(sub), 0)) == 7);
    CHECK(getNumerico(latL_obtener_elemento(mv, getLista(v), 0)) == 99);
    CHECK(getNumerico(latL_obtener_elemento(mv, getLista(v), 1)) == 16);
    CHECK(getNumerico(latL_obtener_elemento(mv, fija, 0)) == 42);
}

static void muestra(lat_mv *mv, memoria_api api, long i, double inicio,
                    double pausa, double pausa_max, double pausas_total,
                    size_t recuperadas, size_t bytes_recuperados, size_t maximo) {
    struct rusage uso;
    CHECK(getrusage(RUSAGE_SELF, &uso) == 0);
    printf("{\"operaciones\":%ld,\"bytes_vm\":%zu,\"pico_bytes_vm\":%zu,"
           "\"rss_kib\":%zu,\"pico_rss_kib\":%ld,\"segundos\":%.9f,"
           "\"pausa_ms\":%.6f,\"pausa_max_ms\":%.6f,\"pausas_total_ms\":%.6f,"
           "\"reservas_recuperadas\":%zu,\"bytes_recuperados\":%zu,",
           i, mv->memoria_usada, maximo, rss_kib(), uso.ru_maxrss,
           reloj() - inicio, pausa * 1000, pausa_max * 1000, pausas_total * 1000,
           recuperadas, bytes_recuperados);
    if (api.medir) {
        latG_medicion m;
        CHECK(api.medir(mv, &m) == LAT_G_OK);
        printf("\"reservas_registradas\":%zu,\"bytes_registrados\":%zu,"
               "\"fijados\":%zu,\"pico_latM\":%zu}\n", m.reservas_registradas,
               m.bytes_registrados, m.fijados, m.pico_bytes_vm);
    } else {
        puts("\"reservas_registradas\":null,\"bytes_registrados\":null,\"fijados\":null,\"pico_latM\":null}");
    }
}

int main(int argc, char **argv) {
    if ((argc != 3 && argc != 4) || (strcmp(argv[1], "base") && strcmp(argv[1], "recolectar"))) return 3;
    bool activa = !strcmp(argv[1], "recolectar");
    char *fin;
    long vueltas = strtol(argv[2], &fin, 10);
    if (!*argv[2] || *fin || vueltas < 1000 || vueltas > (argc == 4 ? 10000000 : 100000)) return 3;
    long segundos = 0;
    if (argc == 4) {
        segundos = strtol(argv[3], &fin, 10);
        if (!activa || !*argv[3] || *fin || segundos < 1 || segundos > 1800) return 3;
    }
    setvbuf(stdout, NULL, _IOLBF, 0);
    memoria_api api = cargar_api();
    lat_mv *mv = latC_crear_mv();
    CHECK(mv);
    mv->nombre_archivo = "carga_p04";
    mv->global->REPL = false;
    mictlan_ciencia_ffi_registrar(mv);
    if (activa) {
        CHECK(api.habilitar && api.autorizar && api.retener && api.soltar && api.recolectar && api.medir);
        CHECK(api.habilitar(mv) == LAT_G_OK);
        lat_objeto *suma = latH_obtener(getDic(global(mv, "ciencia")), "sumar2");
        CHECK(suma && suma->tipo == T_CFUN && api.autorizar(mv, getCfun(suma)) == LAT_G_OK);
    }
    programa carga = compilar(mv, "original = ciencia.sumar2(3, 4, 5, 12)\n"
        "alias = original\noriginal = [7, 14]\nalias[0] = 99\n");
    programa error = compilar(mv, "ciencia.sumar2(3, 4, 5, \"texto\")\n");
    lista *fija = latL_crear(mv);
    lat_objeto *contenedor = latC_crear_lista(mv, fija);
    latL_agregar(mv, fija, latC_crear_numerico(mv, 42));
    latM_liberar(mv, contenedor);
    if (activa) {
        CHECK(api.retener(mv, carga.funcion) == LAT_G_OK);
        CHECK(api.retener(mv, error.funcion) == LAT_G_OK);
        CHECK(api.retener(mv, fija) == LAT_G_OK);
    }
    double inicio = reloj(), pausa_max = 0, pausas_total = 0;
    size_t recuperadas = 0, bytes_recuperados = 0, maximo = mv->memoria_usada;
    size_t meseta = 0;
    for (long i = 1; i <= vueltas; ++i) {
        if (i % 1000 == 0) CHECK(latC_llamar_funcion(mv, error.funcion) == LAT_ERRRUN);
        CHECK(latC_llamar_funcion(mv, carga.funcion) == 0);
        CHECK(mv->ptrpila == 0 && mv->ptrctx == 0 && mv->numejec == 0 && mv->tope == mv->pila);
        guardar_diccionario(mv, global(mv, "alias"));
        if (mv->memoria_usada > maximo) maximo = mv->memoria_usada;
        double pausa = 0;
        if (activa && (i % 100 == 0 || i == vueltas)) {
            double t = reloj();
            CHECK(api.recolectar(mv) == LAT_G_OK);
            pausa = reloj() - t;
            if (pausa > pausa_max) pausa_max = pausa;
            pausas_total += pausa;
            latG_medicion m;
            CHECK(api.medir(mv, &m) == LAT_G_OK);
            recuperadas += m.reservas_recuperadas;
            bytes_recuperados += m.bytes_recuperados;
            if (i == 1000) meseta = m.bytes_vm;
            if (i > 1000) CHECK(m.bytes_vm <= meseta + 8192);
        }
        bool duracion_cumplida = segundos && i % 100 == 0 && reloj() - inicio >= (double)segundos;
        if (i == 100 || i == 1000 || i == 10000 || i == vueltas || duracion_cumplida ||
            (segundos && i % 100000 == 0)) {
            comprobar(mv, fija);
            muestra(mv, api, i, inicio, pausa, pausa_max, pausas_total,
                    recuperadas, bytes_recuperados, maximo);
        }
        if (duracion_cumplida) break;
    }
    CHECK(!segundos || reloj() - inicio >= (double)segundos);
    if (activa) {
        CHECK(api.soltar(mv, fija) == LAT_G_OK);
        CHECK(api.soltar(mv, carga.funcion) == LAT_G_OK);
        CHECK(api.soltar(mv, error.funcion) == LAT_G_OK);
        CHECK(api.recolectar(mv) == LAT_G_OK && recuperadas > 0);
    } else {
        latO_destruir(mv, carga.funcion);
        latO_destruir(mv, error.funcion);
    }
    latA_destruir(carga.arbol);
    latA_destruir(error.arbol);
    latC_destruir_mv(mv);
    return 0;
}

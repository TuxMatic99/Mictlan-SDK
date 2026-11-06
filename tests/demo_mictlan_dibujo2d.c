
#include <stdio.h>
#include "raylib.h"
#include "mictlan_dibujo2d.h"
#include "mictlan_render_raylib.h"

int main(void)
{
    // Preparar nuestro lienzo
    MictlanLienzo lienzo;
    mictlan_lienzo_inicializar(&lienzo);

    // Agregar un círculo naranja
    bool correcto = mictlan_lienzo_agregar_circulo(
        &lienzo,
        450, 300, 60,
        230, 110, 60, 255
    );

    if (!correcto) {
        fprintf(stderr, "Error al crear el circulo\n");
        return 1;
    }

    // Abrir ventana
    InitWindow(900, 600, "Mictlan - Dibujo 2D");

    if (!IsWindowReady()) {
        fprintf(stderr, "No se pudo abrir la ventana\n");
        return 1;
    }

    SetTargetFPS(60);

    // Bucle gráfico
    while (!WindowShouldClose()) {

        BeginDrawing();

        ClearBackground(RAYWHITE);

        mictlan_renderizar_lienzo(&lienzo);

        DrawText(
            "Mi primer circulo en Mictlan",
            24, 24, 24, DARKBLUE
        );

        EndDrawing();
    }

    CloseWindow();

    return 0;
}

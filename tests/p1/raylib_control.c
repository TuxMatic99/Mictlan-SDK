#include "raylib.h"

int main(void)
{
    InitWindow(760, 480, "Control Raylib P1");
    if (!IsWindowReady()) return 1;
    SetExitKey(KEY_NULL);
    SetTargetFPS(60);
    while (!WindowShouldClose()) {
        BeginDrawing();
        ClearBackground(RAYWHITE);
        DrawText("Control independiente de Mictlan", 20, 20, 24, DARKBLUE);
        EndDrawing();
    }
    CloseWindow();
    return 0;
}

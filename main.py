import flet as ft
import asyncio
import os
from datetime import datetime

# Componente personalizado para cada bombero en la zona caliente
class BomberoActivo(ft.Container):
    def __init__(self, nombre, on_exit):
        super().__init__()
        self.nombre = nombre
        self.on_exit = on_exit # Función para devolverlo a la lista de disponibles
        self.hora_entrada = datetime.now()
        self.ultima_revision = datetime.now()
        self.activo = True

        # Elementos de la UI
        self.texto_cronometro = ft.Text("00:00", size=22, weight="bold", font_family="monospace")
        self.input_aire = ft.TextField(
            label="Presión (bar)", 
            width=100, 
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True
        )
        self.btn_actualizar = ft.IconButton(
            icon=ft.icons.CHECK_CIRCLE, 
            icon_color=ft.colors.GREEN_400,
            tooltip="Registrar presión y resetear aviso",
            on_click=self.actualizar_aire
        )

        # Diseño de la fila
        self.content = ft.Row([
            ft.Text(f"{self.nombre}", width=130, size=18, weight="bold"),
            ft.Text(f"Entrada: {self.hora_entrada.strftime('%H:%M')}", width=100),
            self.texto_cronometro,
            ft.Row([self.input_aire, self.btn_actualizar], spacing=0),
            ft.ElevatedButton("Salir", on_click=self.salir, color=ft.colors.WHITE, bgcolor=ft.colors.RED_700)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.padding = 15
        self.border_radius = 8
        self.bgcolor = ft.colors.BLUE_GREY_900

    # Se ejecuta automáticamente al añadir el componente a la pantalla
    def did_mount(self):
        self.page.run_task(self.actualizar_reloj)

    # Se ejecuta automáticamente al eliminar el componente de la pantalla
    def will_unmount(self):
        self.activo = False

    # Tarea asíncrona independiente para cada bombero
    async def actualizar_reloj(self):
        while self.activo:
            ahora = datetime.now()
            
            # Cálculo del tiempo total
            tiempo_total = ahora - self.hora_entrada
            minutos, segundos = divmod(int(tiempo_total.total_seconds()), 60)
            self.texto_cronometro.value = f"{minutos:02d}:{segundos:02d}"

            # Lógica de la alarma (5 minutos = 300 segundos)
            tiempo_sin_revisar = ahora - self.ultima_revision
            if tiempo_sin_revisar.total_seconds() >= 300: 
                self.bgcolor = ft.colors.RED_900
            else:
                self.bgcolor = ft.colors.BLUE_GREY_900

            self.update()
            await asyncio.sleep(1)

    def actualizar_aire(self, e):
        if self.input_aire.value:
            self.ultima_revision = datetime.now()
            self.bgcolor = ft.colors.BLUE_GREY_900
            self.update()

    def salir(self, e):
        self.activo = False
        self.on_exit(self)


def main(page: ft.Page):
    page.title = "Control de Accesos ERA"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    lista_disponibles = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    lista_activos = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def agregar_bombero(e):
        if input_nombre.value:
            crear_fila_disponible(input_nombre.value)
            input_nombre.value = ""
            input_nombre.focus()
            page.update()

    def crear_fila_disponible(nombre):
        def entrar(e):
            lista_disponibles.controls.remove(fila)
            nuevo_activo = BomberoActivo(nombre, on_exit=salir_intervencion)
            lista_activos.controls.append(nuevo_activo)
            page.update()

        fila = ft.Container(
            content=ft.Row([
                ft.Text(nombre, width=150, size=16),
                ft.IconButton(icon=ft.icons.LOGIN, icon_color=ft.colors.BLUE_400, tooltip="Entrar a intervención", on_click=entrar)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            border_radius=8,
            bgcolor=ft.colors.SURFACE_VARIANT
        )
        lista_disponibles.controls.append(fila)

    def salir_intervencion(bombero_activo):
        lista_activos.controls.remove(bombero_activo)
        crear_fila_disponible(bombero_activo.nombre)
        page.update()

    # Panel izquierdo: Añadir y listar disponibles
    input_nombre = ft.TextField(label="Nombre del efectivo", expand=True, on_submit=agregar_bombero)
    btn_agregar = ft.ElevatedButton("Añadir", on_click=agregar_bombero, height=50)

    panel_izquierdo = ft.Container(
        content=ft.Column([
            ft.Text("Efectivos Disponibles", size=20, weight="bold"),
            ft.Row([input_nombre, btn_agregar]),
            ft.Divider(),
            lista_disponibles
        ]),
        width=350,
        padding=20,
        border=ft.border.all(1, ft.colors.OUTLINE),
        border_radius=10,
    )

    # Panel derecho: Control de la intervención
    panel_derecho = ft.Container(
        content=ft.Column([
            ft.Text("Intervención Activa (Control ERA)", size=20, weight="bold"),
            ft.Divider(),
            lista_activos
        ]),
        expand=True,
        padding=20,
        border=ft.border.all(1, ft.colors.OUTLINE),
        border_radius=10
    )

    page.add(
        ft.Row([panel_izquierdo, panel_derecho], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
    )

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=puerto)

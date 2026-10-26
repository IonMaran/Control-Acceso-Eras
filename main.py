import flet as ft
import asyncio
import os
from datetime import datetime

# Componente personalizado para cada bombero en la zona caliente
class BomberoActivo(ft.Container):
    def __init__(self, nombre, tiempo_acumulado, on_exit):
        super().__init__()
        self.nombre = nombre
        self.tiempo_acumulado = tiempo_acumulado
        self.on_exit = on_exit
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
        
        # Botón de salir con icono de puerta
        self.btn_salir = ft.IconButton(
            icon=ft.icons.LOGOUT,
            icon_color=ft.colors.RED_400,
            tooltip="Salir de la intervención",
            on_click=self.salir
        )

        # Diseño de la fila
        self.content = ft.Row([
            ft.Text(f"{self.nombre}", width=130, size=18, weight="bold"),
            ft.Text(f"Entrada: {self.hora_entrada.strftime('%H:%M')}", width=100),
            self.texto_cronometro,
            ft.Row([self.input_aire, self.btn_actualizar], spacing=0),
            self.btn_salir
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.padding = 15
        self.border_radius = 8
        self.bgcolor = ft.colors.BLUE_GREY_900

    def did_mount(self):
        self.page.run_task(self.actualizar_reloj)

    def will_unmount(self):
        self.activo = False

    async def actualizar_reloj(self):
        ticks = 0
        color_naranja_suave = "#9C5C1E"
        
        while self.activo:
            ahora = datetime.now()
            
            tiempo_total = ahora - self.hora_entrada
            minutos, segundos = divmod(int(tiempo_total.total_seconds()), 60)
            self.texto_cronometro.value = f"{minutos:02d}:{segundos:02d}"

            tiempo_sin_revisar = ahora - self.ultima_revision
            segundos_sin_revisar = tiempo_sin_revisar.total_seconds()

            if segundos_sin_revisar >= 600: # 10 min reales (cambiar a 40 para pruebas)
                self.bgcolor = ft.colors.RED_900 if ticks % 2 == 0 else ft.colors.BLUE_GREY_900
            elif segundos_sin_revisar >= 300: # 5 min reales (cambiar a 20 para pruebas)
                self.bgcolor = color_naranja_suave if ticks % 4 < 2 else ft.colors.BLUE_GREY_900
            else:
                self.bgcolor = ft.colors.BLUE_GREY_900

            self.update()
            ticks += 1
            await asyncio.sleep(0.5)

    def actualizar_aire(self, e):
        if self.input_aire.value:
            self.ultima_revision = datetime.now()
            self.bgcolor = ft.colors.BLUE_GREY_900
            self.update()

    def salir(self, e):
        self.activo = False
        minutos_sesion = (datetime.now() - self.hora_entrada).total_seconds() / 60
        minutos_totales = int(self.tiempo_acumulado + minutos_sesion)
        self.on_exit(self, minutos_totales)


def main(page: ft.Page):
    page.title = "Control de Accesos ERA"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    lista_disponibles = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    lista_activos = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def agregar_bombero(e):
        if input_nombre.value:
            crear_fila_disponible(input_nombre.value, 0)
            input_nombre.value = ""
            input_nombre.focus()
            page.update()

    def crear_fila_disponible(nombre, minutos_acumulados):
        def entrar(e):
            lista_disponibles.controls.remove(fila)
            nuevo_activo = BomberoActivo(nombre, minutos_acumulados, on_exit=salir_intervencion)
            lista_activos.controls.append(nuevo_activo)
            page.update()

        texto_minutos = ft.Text(f"{minutos_acumulados} min", color=ft.colors.WHITE70, size=15, italic=True)
        if minutos_acumulados == 0:
            texto_minutos.visible = False

        fila = ft.Container(
            content=ft.Row([
                ft.Text(nombre, width=150, size=16),
                ft.Row([
                    texto_minutos,
                    ft.IconButton(icon=ft.icons.LOGIN, icon_color=ft.colors.BLUE_400, tooltip="Entrar a intervención", on_click=entrar)
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            border_radius=8,
            bgcolor=ft.colors.SURFACE_VARIANT
        )
        lista_disponibles.controls.append(fila)

    def salir_intervencion(bombero_activo, minutos_totales):
        lista_activos.controls.remove(bombero_activo)
        crear_fila_disponible(bombero_activo.nombre, minutos_totales)
        page.update()

    def borrar_todo(e):
        for bombero in lista_activos.controls:
            bombero.activo = False
        
        lista_activos.controls.clear()
        lista_disponibles.controls.clear()
        page.update()

    # Panel izquierdo (Ocupa 12 columnas en móviles, 4 en pantallas grandes)
    input_nombre = ft.TextField(label="Nombre del efectivo", expand=True, on_submit=agregar_bombero)
    btn_agregar = ft.ElevatedButton("Añadir", on_click=agregar_bombero, height=50)

    panel_izquierdo = ft.Container(
        content=ft.Column([
            ft.Text("Efectivos Disponibles", size=20, weight="bold"),
            ft.Row([input_nombre, btn_agregar]),
            ft.Divider(),
            lista_disponibles
        ], expand=True),
        padding=20,
        border=ft.border.all(1, ft.colors.OUTLINE),
        border_radius=10,
        col={"xs": 12, "lg": 4},
        height=400 # Altura fija en móvil para que no colapse
    )

    # Panel derecho (Ocupa 12 columnas en móviles, 8 en pantallas grandes)
    panel_derecho = ft.Container(
        content=ft.Column([
            ft.Text("Intervención Activa", size=20, weight="bold"),
            ft.Divider(),
            lista_activos
        ], expand=True),
        padding=20,
        border=ft.border.all(1, ft.colors.OUTLINE),
        border_radius=10,
        col={"xs": 12, "lg": 8},
        height=500 # Altura fija en móvil para que se vea completo
    )

    # Cabecera principal
    btn_borrar_todo = ft.ElevatedButton(
        "Borrar Todo", 
        icon=ft.icons.DELETE, 
        color=ft.colors.WHITE, 
        bgcolor=ft.colors.BLUE_GREY_900,
        on_click=borrar_todo
    )
    
    cabecera = ft.Row([
        ft.Text("Control de Accesos ERA", size=28, weight="bold"),
        btn_borrar_todo
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # Diseño adaptable con ResponsiveRow
    page.add(
        cabecera,
        ft.ResponsiveRow([
            panel_izquierdo,
            panel_derecho
        ], expand=True)
    )

if __name__ == "__main__":
    puerto = os.environ.get("PORT")
    if puerto:
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=int(puerto))
    else:
        ft.app(target=main)

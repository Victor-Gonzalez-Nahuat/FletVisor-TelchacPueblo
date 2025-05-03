import flet as ft
import datetime
import requests

API_URL = "https://api-telchac-pueblo-production.up.railway.app/"

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.colors.RED)
    page.title = "Recibos"
    page.padding = 10

    todos_los_recibos = []
    pagina_actual = 0
    tamanio_pagina = 100


    hoy = datetime.date.today()
    hoy_str = hoy.isoformat()

    logo = ft.Image(
        src="https://i.ibb.co/B2P6S92b/458175466-1548600749422923-6541739542313811862-n.jpg",
        width=60, height=60, fit=ft.ImageFit.CONTAIN
    )

    titulo_empresa = ft.Text("TELCHAC PUEBLO", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
    titulo = ft.Text("Consulta de Recibos", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)

    txt_fecha_desde = ft.TextField(label="Desde", read_only=True, width=150,
                                   value=hoy.strftime("%d-%m-%Y"), bgcolor=ft.colors.WHITE)
    txt_fecha_desde.data = hoy_str

    txt_fecha_hasta = ft.TextField(label="Hasta", read_only=True, width=150,
                                   value=hoy.strftime("%d-%m-%Y"), bgcolor=ft.colors.WHITE)
    txt_fecha_hasta.data = hoy_str

    def actualizar_fecha(txt, nueva_fecha):
        txt.data = nueva_fecha
        txt.value = datetime.datetime.fromisoformat(nueva_fecha).strftime("%d-%m-%Y")
        page.update()

    date_picker_desde = ft.DatePicker(on_change=lambda e: actualizar_fecha(txt_fecha_desde, e.data))
    date_picker_hasta = ft.DatePicker(on_change=lambda e: actualizar_fecha(txt_fecha_hasta, e.data))
    page.overlay.extend([date_picker_desde, date_picker_hasta])

    fecha_desde_btn = ft.ElevatedButton("Fecha desde", icon=ft.icons.CALENDAR_MONTH,
                                        on_click=lambda e: page.open(date_picker_desde))
    fecha_hasta_btn = ft.ElevatedButton("Fecha hasta", icon=ft.icons.CALENDAR_MONTH,
                                        on_click=lambda e: page.open(date_picker_hasta))

    contribuyente_input = ft.TextField(
        label="Filtrar por contribuyente (opcional)",
        width=400,
        text_size=14,
        border_color=ft.colors.GREY,
        color=ft.colors.BLACK,
        cursor_color=ft.colors.BLACK
    )

    buscar_btn = ft.ElevatedButton("Buscar",
        width=300, height=40, icon=ft.icons.SEARCH,
        bgcolor=ft.colors.GREEN, color=ft.colors.WHITE
    )
    buscar_btn.on_click = lambda e: buscar_producto(contribuyente_input.value)

    encabezado = ft.Container(
        content=ft.Column([
            ft.Row([logo, titulo_empresa]),
            titulo,
            ft.Row([fecha_desde_btn, fecha_hasta_btn]),
            ft.Row([txt_fecha_desde, txt_fecha_hasta]),
            ft.Row([buscar_btn], alignment=ft.MainAxisAlignment.START),
            contribuyente_input
        ]),
        padding=20,
        bgcolor="#ff6038",
        border_radius=ft.BorderRadius(0, 0, 20, 20)
    )

    resultado_card = ft.Container(content=ft.Column([], scroll=ft.ScrollMode.AUTO, height=200), padding=10)
    totales_card = ft.Container()
    loader = ft.ProgressRing(visible=False, color=ft.colors.ORANGE, stroke_width=4)

    def formatear_fecha_yymmdd(f):
        try:
            return datetime.datetime.strptime(f, "%y%m%d").strftime("%d-%m-%Y")
        except:
            return f
        
    def cambiar_pagina(delta):
        nonlocal pagina_actual
        pagina_actual += delta
        mostrar_pagina()
        
    def mostrar_resultados(data):
        nonlocal todos_los_recibos, pagina_actual
        todos_los_recibos = data
        pagina_actual = 0
        mostrar_pagina()

    def mostrar_pagina():
        nonlocal pagina_actual, tamanio_pagina, todos_los_recibos

        inicio = pagina_actual * tamanio_pagina
        fin = inicio + tamanio_pagina
        fragmento = todos_los_recibos[inicio:fin]

        recibos_widgets = []

        for r in fragmento:
            es_cancelado = r.get("status", r.get("id_status", "0")) == "1"
            color_texto = ft.colors.GREY if es_cancelado else ft.colors.BLACK
            estado = "❌ CANCELADO" if es_cancelado else ""

            tarjeta = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Recibo: {r['recibo']} {estado}", weight=ft.FontWeight.BOLD, size=18, color=color_texto),
                        ft.Text(f"Contribuyente: {r['contribuyente']}", color=color_texto),
                        ft.Text(f"Concepto: {r['concepto']}", color=color_texto),
                        ft.Text(f"Fecha: {formatear_fecha_yymmdd(r['fecha'])}", color=color_texto),
                        ft.Text(f"Neto: ${float(r['neto']):,.2f}", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_800 if not es_cancelado else ft.colors.GREY),
                        ft.Text(f"Descuento: ${float(r['descuento']):,.2f}", color=color_texto)
                    ]),
                    padding=15,
                    bgcolor=ft.colors.WHITE,
                    border_radius=10,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.GREY_400, offset=ft.Offset(2, 2))
                ),
                elevation=2
            )
            recibos_widgets.append(tarjeta)

        botones_navegacion = []

        if pagina_actual > 0:
            botones_navegacion.append(ft.ElevatedButton("⬅️ Anteriores 100", on_click=lambda e: cambiar_pagina(-1)))

        if fin < len(todos_los_recibos):
            botones_navegacion.append(ft.ElevatedButton("Siguientes 100 ➡️", on_click=lambda e: cambiar_pagina(1)))

        resultado_card.content = ft.Column(
            recibos_widgets + [ft.Row(botones_navegacion, alignment=ft.MainAxisAlignment.CENTER)],
            spacing=10, scroll=ft.ScrollMode.ALWAYS, height=200
        )
        page.update()
    def buscar_producto(nombre_raw):
        buscar_btn.disabled = True
        loader.visible = True
        fecha_desde_btn.disabled = True
        fecha_hasta_btn.disabled = True
        page.update()

        desde = txt_fecha_desde.data.replace("-", "")[2:]
        hasta = txt_fecha_hasta.data.replace("-", "")[2:]
        params = {"desde": desde, "hasta": hasta}

        nombre = nombre_raw.strip()
        if nombre:
            params["contribuyente"] = nombre

        cancelados = 0
        data = []

        try:
            url = f"{API_URL}recibos/filtrar" if "contribuyente" in params else f"{API_URL}recibos"
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                cancelados = sum(1 for r in data if r.get("status", r.get("id_status", "0")) == "1")
                mostrar_resultados(data)
            else:
                print("Error:", response.status_code, response.json().get("detail"))
        except Exception as e:
            print("Error al buscar recibos:", str(e))

        try:
            response_totales = requests.get(f"{API_URL}recibos/totales", params=params)
            if response_totales.status_code == 200:
                d = response_totales.json()
                totales_card.content = ft.Column([
                    ft.Text(f"Total Neto: ${float(d.get('total_neto', 0)):,.2f}", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Total Descuento: ${float(d.get('total_descuento', 0)):,.2f}", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Recibos encontrados: {len(data)}", size=14, color=ft.colors.BLACK),
                    ft.Text(f"Recibos cancelados: {cancelados}", size=14, color=ft.colors.RED_700)
                ])
        except Exception as e:
            print("Error al obtener totales:", str(e))

        loader.visible = False
        buscar_btn.disabled = False
        fecha_hasta_btn.disabled = False
        fecha_desde_btn.disabled = False
        page.update()

    page.add(
        ft.Column([
            encabezado,
            loader,
            totales_card,
            resultado_card,
        ], spacing=20)
    )

    buscar_producto("")

ft.app(target=main)
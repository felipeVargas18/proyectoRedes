import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import json
from collections import deque
from datetime import datetime
import uuid
from matplotlib.lines import Line2D


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="App SOS - Red LoRa Ad Hoc",
    layout="wide"
)

PRIORIDAD_VALOR = {
    "Alta": 1,
    "Media": 2,
    "Baja": 3
}

TIPOS_EMERGENCIA = {
    "Emergencia médica": {
        "prioridad": "Alta",
        "mensaje": "Se requiere atención médica urgente."
    },
    "Incendio": {
        "prioridad": "Alta",
        "mensaje": "Se reporta incendio en la zona."
    },
    "Inundación": {
        "prioridad": "Alta",
        "mensaje": "Se requiere apoyo por inundación."
    },
    "Persona desaparecida": {
        "prioridad": "Media",
        "mensaje": "Se reporta una persona desaparecida."
    },
    "Vía bloqueada": {
        "prioridad": "Media",
        "mensaje": "Se reporta una vía bloqueada."
    },
    "Solicitud de alimentos/agua": {
        "prioridad": "Baja",
        "mensaje": "Se solicita apoyo con alimentos o agua."
    }
}

st.subheader("Paquete desde app Flutter")

usar_json_flutter = st.checkbox(
    "Usar paquete JSON generado por la app Flutter",
    value=False
)

json_flutter = ""

if usar_json_flutter:
    json_flutter = st.text_area(
        "Pega aquí el paquete JSON de Flutter",
        height=180
    )
# ============================================================
# CREACIÓN DE LA RED LORA SIMULADA
# ============================================================

def crear_red_lora():
    """
    Crea una red ad hoc simulada.
    Cada nodo representa un posible dispositivo LoRa comunitario.
    """

    G = nx.Graph()

    nodos = [
        "N1 - Usuario comunidad",
        "N2 - Casa rural",
        "N3 - Escuela",
        "N4 - Puesto médico",
        "N5 - Repetidor cerro",
        "N6 - Brigadista",
        "N7 - Vereda norte",
        "N8 - Centro de ayuda"
    ]

    enlaces = [
        ("N1 - Usuario comunidad", "N2 - Casa rural"),
        ("N1 - Usuario comunidad", "N3 - Escuela"),

        ("N2 - Casa rural", "N3 - Escuela"),
        ("N2 - Casa rural", "N5 - Repetidor cerro"),

        ("N3 - Escuela", "N5 - Repetidor cerro"),
        ("N3 - Escuela", "N7 - Vereda norte"),

        ("N5 - Repetidor cerro", "N4 - Puesto médico"),
        ("N5 - Repetidor cerro", "N6 - Brigadista"),
        ("N5 - Repetidor cerro", "N8 - Centro de ayuda"),

        ("N7 - Vereda norte", "N6 - Brigadista"),

        ("N6 - Brigadista", "N8 - Centro de ayuda"),
        ("N4 - Puesto médico", "N8 - Centro de ayuda")
    ]

    G.add_nodes_from(nodos)
    G.add_edges_from(enlaces)

    return G


def posiciones_red():
    """
    Posiciones fijas para que el gráfico no cambie en cada ejecución.
    """

    return {
        "N1 - Usuario comunidad": (-2.2, 0.1),
        "N2 - Casa rural": (-1.2, 1.1),
        "N3 - Escuela": (-1.2, -0.9),
        "N5 - Repetidor cerro": (0.2, 0.1),
        "N7 - Vereda norte": (-0.1, -1.8),
        "N4 - Puesto médico": (1.5, 1.1),
        "N6 - Brigadista": (1.4, -0.9),
        "N8 - Centro de ayuda": (2.6, 0.1)
    }


# ============================================================
# ALGORITMO: FLOODING CONTROLADO
# ============================================================

def propagacion_flooding_controlado(G, paquete, nodos_caidos, detener_al_entregar=False):
    """
    Simula una propagación distribuida tipo flooding controlado.

    Reglas:
    1. El nodo origen transmite a sus vecinos.
    2. Cada nodo reenvía si:
       - no está caído,
       - no había visto el ID del mensaje,
       - el TTL no llegó a cero.
    3. Si un nodo recibe un ID repetido, descarta el duplicado.
    4. Si el mensaje llega al destino, se marca como entregado.
    """

    origen = paquete["origen"]
    destino = paquete["destino"]
    ttl_inicial = paquete["ttl"]
    id_mensaje = paquete["id"]

    logs = []
    nodos_recibieron = set()
    nodos_reenviaron = set()
    nodos_duplicados = set()
    enlaces_transmitidos = []
    enlaces_duplicados = []

    entregado = False
    ruta_entrega = None
    duplicados_descartados = 0
    transmisiones = 0
    descartes_ttl = 0

    # Validaciones iniciales
    if origen in nodos_caidos:
        logs.append({
            "paso": 0,
            "nodo": origen,
            "evento": "Fallo",
            "ttl": ttl_inicial,
            "detalle": "El nodo origen está caído. No se puede enviar la alerta."
        })

        return {
            "entregado": False,
            "ruta_entrega": None,
            "nodos_recibieron": nodos_recibieron,
            "nodos_reenviaron": nodos_reenviaron,
            "nodos_duplicados": nodos_duplicados,
            "enlaces_transmitidos": enlaces_transmitidos,
            "enlaces_duplicados": enlaces_duplicados,
            "duplicados_descartados": duplicados_descartados,
            "transmisiones": transmisiones,
            "descartes_ttl": descartes_ttl,
            "logs": logs
        }

    if destino in nodos_caidos:
        logs.append({
            "paso": 0,
            "nodo": destino,
            "evento": "Advertencia",
            "ttl": ttl_inicial,
            "detalle": "El nodo destino está caído. La red puede propagar, pero no entregar."
        })

    # Cada nodo guarda los IDs ya vistos.
    # En esta simulación se usa un conjunto global para representar el estado distribuido.
    mensajes_vistos = set()

    cola = deque()
    cola.append((origen, [origen], ttl_inicial))

    mensajes_vistos.add((origen, id_mensaje))
    nodos_recibieron.add(origen)

    logs.append({
        "paso": 0,
        "nodo": origen,
        "evento": "Generación",
        "ttl": ttl_inicial,
        "detalle": f"Se genera el paquete {id_mensaje} con prioridad {paquete['prioridad']}."
    })

    paso = 1

    while cola:
        nodo_actual, ruta_actual, ttl_actual = cola.popleft()

        if nodo_actual == destino:
            entregado = True

            if ruta_entrega is None:
                ruta_entrega = ruta_actual

            logs.append({
                "paso": paso,
                "nodo": nodo_actual,
                "evento": "Entregado",
                "ttl": ttl_actual,
                "detalle": "El paquete llegó al nodo destino."
            })
            paso += 1

            if detener_al_entregar:
                break

            # El destino no necesita seguir reenviando.
            continue

        if ttl_actual <= 0:
            descartes_ttl += 1

            logs.append({
                "paso": paso,
                "nodo": nodo_actual,
                "evento": "TTL agotado",
                "ttl": ttl_actual,
                "detalle": "El nodo no reenvía porque el TTL llegó a cero."
            })
            paso += 1
            continue

        if nodo_actual in nodos_caidos:
            logs.append({
                "paso": paso,
                "nodo": nodo_actual,
                "evento": "Nodo caído",
                "ttl": ttl_actual,
                "detalle": "El nodo no puede reenviar porque está fuera de servicio."
            })
            paso += 1
            continue

        vecinos = list(G.neighbors(nodo_actual))
        vecinos.sort()

        if len(vecinos) == 0:
            logs.append({
                "paso": paso,
                "nodo": nodo_actual,
                "evento": "Sin vecinos",
                "ttl": ttl_actual,
                "detalle": "El nodo no tiene vecinos disponibles para reenviar."
            })
            paso += 1
            continue

        nodos_reenviaron.add(nodo_actual)

        logs.append({
            "paso": paso,
            "nodo": nodo_actual,
            "evento": "Reenvío",
            "ttl": ttl_actual,
            "detalle": f"El nodo intenta reenviar a {len(vecinos)} vecino(s)."
        })
        paso += 1

        for vecino in vecinos:

            if vecino in nodos_caidos:
                logs.append({
                    "paso": paso,
                    "nodo": vecino,
                    "evento": "No disponible",
                    "ttl": ttl_actual - 1,
                    "detalle": f"{nodo_actual} intenta enviar, pero el vecino está caído."
                })
                paso += 1
                continue

            transmisiones += 1

            # Si el vecino ya vio ese mensaje, descarta duplicado
            if (vecino, id_mensaje) in mensajes_vistos:
                duplicados_descartados += 1
                nodos_duplicados.add(vecino)
                enlaces_duplicados.append((nodo_actual, vecino))

                logs.append({
                    "paso": paso,
                    "nodo": vecino,
                    "evento": "Duplicado descartado",
                    "ttl": ttl_actual - 1,
                    "detalle": f"El nodo ya había recibido el paquete {id_mensaje}."
                })
                paso += 1
                continue

            # Primera vez que el vecino ve el mensaje
            mensajes_vistos.add((vecino, id_mensaje))
            nodos_recibieron.add(vecino)
            enlaces_transmitidos.append((nodo_actual, vecino))

            nueva_ruta = ruta_actual + [vecino]
            nuevo_ttl = ttl_actual - 1

            logs.append({
                "paso": paso,
                "nodo": vecino,
                "evento": "Recepción",
                "ttl": nuevo_ttl,
                "detalle": f"Recibe paquete desde {nodo_actual}."
            })
            paso += 1

            cola.append((vecino, nueva_ruta, nuevo_ttl))

    return {
        "entregado": entregado,
        "ruta_entrega": ruta_entrega,
        "nodos_recibieron": nodos_recibieron,
        "nodos_reenviaron": nodos_reenviaron,
        "nodos_duplicados": nodos_duplicados,
        "enlaces_transmitidos": enlaces_transmitidos,
        "enlaces_duplicados": enlaces_duplicados,
        "duplicados_descartados": duplicados_descartados,
        "transmisiones": transmisiones,
        "descartes_ttl": descartes_ttl,
        "logs": logs
    }


# ============================================================
# VISUALIZACIÓN DE LA RED
# ============================================================

def dibujar_red(G, resultado=None, nodos_caidos=None, origen=None, destino=None):
    if nodos_caidos is None:
        nodos_caidos = []

    pos = posiciones_red()

    fig, ax = plt.subplots(figsize=(11, 6.8))

    # Enlaces base
    nx.draw_networkx_edges(
        G,
        pos,
        ax=ax,
        width=1.2,
        edge_color="#B0B0B0",
        alpha=0.55
    )

    # Enlaces por donde se propagó el mensaje
    if resultado is not None:
        enlaces_transmitidos = resultado["enlaces_transmitidos"]
        enlaces_duplicados = resultado["enlaces_duplicados"]

        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=enlaces_transmitidos,
            ax=ax,
            width=3.5,
            edge_color="#1f77b4",
            alpha=0.9
        )

        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=enlaces_duplicados,
            ax=ax,
            width=2,
            edge_color="#ff7f0e",
            alpha=0.75,
            style="dashed"
        )

        if resultado["ruta_entrega"] is not None:
            ruta = resultado["ruta_entrega"]
            enlaces_ruta = list(zip(ruta, ruta[1:]))

            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=enlaces_ruta,
                ax=ax,
                width=5.5,
                edge_color="#2ca02c",
                alpha=0.95
            )

    nodos = list(G.nodes)
    nodos_caidos_set = set(nodos_caidos)

    nodos_recibieron = set()
    nodos_reenviaron = set()
    nodos_duplicados = set()

    if resultado is not None:
        nodos_recibieron = resultado["nodos_recibieron"]
        nodos_reenviaron = resultado["nodos_reenviaron"]
        nodos_duplicados = resultado["nodos_duplicados"]

    # Clasificación de nodos
    nodos_normales = []
    nodos_rec = []
    nodos_reenv = []
    nodos_dup = []
    nodos_fail = []

    for n in nodos:
        if n in nodos_caidos_set:
            nodos_fail.append(n)
        elif n == origen:
            continue
        elif n == destino:
            continue
        elif n in nodos_duplicados:
            nodos_dup.append(n)
        elif n in nodos_reenviaron:
            nodos_reenv.append(n)
        elif n in nodos_recibieron:
            nodos_rec.append(n)
        else:
            nodos_normales.append(n)

    nx.draw_networkx_nodes(
        G, pos,
        nodelist=nodos_normales,
        node_color="#E8EEF7",
        edgecolors="#30475E",
        node_size=2100,
        linewidths=1.2,
        ax=ax
    )

    nx.draw_networkx_nodes(
        G, pos,
        nodelist=nodos_rec,
        node_color="#A7C7E7",
        edgecolors="#1f77b4",
        node_size=2200,
        linewidths=1.6,
        ax=ax
    )

    nx.draw_networkx_nodes(
        G, pos,
        nodelist=nodos_reenv,
        node_color="#6FA8DC",
        edgecolors="#0B5394",
        node_size=2300,
        linewidths=1.8,
        ax=ax
    )

    nx.draw_networkx_nodes(
        G, pos,
        nodelist=nodos_dup,
        node_color="#FFD39B",
        edgecolors="#E69138",
        node_size=2200,
        linewidths=1.6,
        ax=ax
    )

    if origen is not None and origen not in nodos_caidos_set:
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=[origen],
            node_color="#B7E4C7",
            edgecolors="#2D6A4F",
            node_size=2500,
            linewidths=2.2,
            ax=ax
        )

    if destino is not None and destino not in nodos_caidos_set:
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=[destino],
            node_color="#FFF3B0",
            edgecolors="#CC9A06",
            node_size=2500,
            linewidths=2.2,
            ax=ax
        )

    if nodos_fail:
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=nodos_fail,
            node_color="#F4A6A6",
            edgecolors="#B00020",
            node_shape="X",
            node_size=2300,
            linewidths=2,
            ax=ax
        )

    labels = {
        n: n.replace(" - ", "\n")
        for n in nodos
    }

    nx.draw_networkx_labels(
        G,
        pos,
        labels=labels,
        font_size=8,
        font_weight="bold",
        ax=ax
    )

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Nodo normal',
               markerfacecolor='#E8EEF7', markeredgecolor='#30475E', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Origen',
               markerfacecolor='#B7E4C7', markeredgecolor='#2D6A4F', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Destino',
               markerfacecolor='#FFF3B0', markeredgecolor='#CC9A06', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Reenvió',
               markerfacecolor='#6FA8DC', markeredgecolor='#0B5394', markersize=12),
        Line2D([0], [0], marker='X', color='w', label='Nodo caído',
               markerfacecolor='#F4A6A6', markeredgecolor='#B00020', markersize=12),
        Line2D([0], [0], color='#2ca02c', lw=4, label='Ruta de entrega'),
        Line2D([0], [0], color='#1f77b4', lw=3, label='Propagación'),
        Line2D([0], [0], color='#ff7f0e', lw=2, linestyle='--', label='Duplicado')
    ]

    ax.legend(
        handles=legend_elements,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=4,
        fontsize=8
    )

    ax.set_title("Red LoRa ad hoc simulada - Propagación multi-salto", fontsize=13)
    ax.axis("off")

    st.pyplot(fig)


# ============================================================
# ESTADO DE LA APLICACIÓN
# ============================================================

if "historial" not in st.session_state:
    st.session_state.historial = []

if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None

if "ultimo_paquete" not in st.session_state:
    st.session_state.ultimo_paquete = None


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>
    .phone-box {
        border: 3px solid #222;
        border-radius: 28px;
        padding: 22px;
        background: linear-gradient(180deg, #f8f9fa 0%, #eef2f3 100%);
        box-shadow: 0px 8px 18px rgba(0,0,0,0.18);
        margin-bottom: 15px;
    }

    .phone-title {
        text-align: center;
        font-size: 1.4rem;
        font-weight: 800;
        color: #202124;
        margin-bottom: 8px;
    }

    .phone-subtitle {
        text-align: center;
        font-size: 0.85rem;
        color: #5f6368;
        margin-bottom: 18px;
    }

    .status-ok {
        background-color: #d8f3dc;
        border-left: 6px solid #2d6a4f;
        padding: 10px;
        border-radius: 8px;
    }

    .status-bad {
        background-color: #ffe5e5;
        border-left: 6px solid #b00020;
        padding: 10px;
        border-radius: 8px;
    }

    .status-info {
        background-color: #e7f0ff;
        border-left: 6px solid #1f77b4;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================

st.title("Prototipo integrado: App SOS + Red LoRa Ad Hoc")

st.write(
    "Este prototipo representa una aplicación de emergencia que genera una alerta SOS "
    "y la transmite sobre una red LoRa/ad hoc simulada. La red usa propagación "
    "multi-salto, TTL, control de duplicados, prioridad de mensajes y tolerancia a fallos."
)

G = crear_red_lora()
nodos = list(G.nodes)

col_app, col_red = st.columns([0.9, 1.6])


# ============================================================
# COLUMNA IZQUIERDA: APP SOS
# ============================================================

with col_app:

    st.markdown('<div class="phone-box">', unsafe_allow_html=True)
    st.markdown('<div class="phone-title">📱 App SOS Rural</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="phone-subtitle">Interfaz de usuario para enviar alertas de emergencia</div>',
        unsafe_allow_html=True
    )

    origen = st.selectbox(
        "Ubicación / nodo del usuario",
        nodos,
        index=0
    )

    destino = st.selectbox(
        "Nodo destino",
        nodos,
        index=nodos.index("N8 - Centro de ayuda")
    )

    tipo_emergencia = st.selectbox(
        "Tipo de emergencia",
        list(TIPOS_EMERGENCIA.keys())
    )

    prioridad_sugerida = TIPOS_EMERGENCIA[tipo_emergencia]["prioridad"]
    mensaje_sugerido = TIPOS_EMERGENCIA[tipo_emergencia]["mensaje"]

    prioridad = st.selectbox(
        "Prioridad del mensaje",
        ["Alta", "Media", "Baja"],
        index=["Alta", "Media", "Baja"].index(prioridad_sugerida)
    )

    mensaje = st.text_area(
        "Mensaje",
        value=mensaje_sugerido,
        height=90
    )

    ttl = st.slider(
        "TTL máximo de saltos",
        min_value=1,
        max_value=8,
        value=5
    )

    detener_al_entregar = st.checkbox(
        "Detener propagación cuando llegue al destino",
        value=False
    )

    enviar_sos = st.button(
        "🚨 ENVIAR SOS",
        type="primary",
        use_container_width=True
    )

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# COLUMNA DERECHA: RED Y CONFIGURACIÓN
# ============================================================

with col_red:

    st.subheader("Configuración de la red simulada")

    escenario = st.selectbox(
        "Escenario de prueba",
        [
            "Sin fallos",
            "Falla del repetidor del cerro",
            "Falla de escuela y vereda norte",
            "Falla parcial cerca del centro de ayuda",
            "Personalizado"
        ]
    )

    escenarios_fallos = {
        "Sin fallos": [],
        "Falla del repetidor del cerro": ["N5 - Repetidor cerro"],
        "Falla de escuela y vereda norte": ["N3 - Escuela", "N7 - Vereda norte"],
        "Falla parcial cerca del centro de ayuda": ["N4 - Puesto médico", "N6 - Brigadista"],
        "Personalizado": []
    }

    if escenario == "Personalizado":
        nodos_caidos = st.multiselect(
            "Selecciona nodos caídos",
            nodos
        )
    else:
        nodos_caidos = escenarios_fallos[escenario]
        st.info(f"Nodos caídos en este escenario: {', '.join(nodos_caidos) if nodos_caidos else 'ninguno'}")


# ============================================================
# EJECUCIÓN DEL ENVÍO SOS
# ============================================================

if enviar_sos:

    if origen == destino:
        st.warning("El nodo origen y el nodo destino no pueden ser el mismo.")
    else:
        id_mensaje = "SOS-" + str(uuid.uuid4())[:8].upper()

        if usar_json_flutter and json_flutter.strip() != "":
            try:
                paquete_flutter = json.loads(json_flutter)

                paquete = {
                    "id": paquete_flutter.get("id", "SOS-" + str(uuid.uuid4())[:8].upper()),
                    "origen": paquete_flutter.get("origen", origen),
                    "destino": paquete_flutter.get("destino", destino),
                    "tipo": paquete_flutter.get("tipo", tipo_emergencia),
                    "prioridad": paquete_flutter.get("prioridad", prioridad),
                    "mensaje": paquete_flutter.get("mensaje", mensaje),
                    "ttl": int(paquete_flutter.get("ttl", ttl)),
                    "hora": paquete_flutter.get("hora", datetime.now().strftime("%H:%M:%S"))
                }

            except Exception as e:
                st.error("El JSON pegado no es válido. Revisa el paquete generado por Flutter.")
                st.stop()

        else:
            id_mensaje = "SOS-" + str(uuid.uuid4())[:8].upper()

            paquete = {
                "id": id_mensaje,
                "origen": origen,
                "destino": destino,
                "tipo": tipo_emergencia,
                "prioridad": prioridad,
                "mensaje": mensaje,
                "ttl": ttl,
                "hora": datetime.now().strftime("%H:%M:%S")
            }

        resultado = propagacion_flooding_controlado(
            G=G,
            paquete=paquete,
            nodos_caidos=nodos_caidos,
            detener_al_entregar=detener_al_entregar
        )

        st.session_state.ultimo_resultado = resultado
        st.session_state.ultimo_paquete = paquete

        if resultado["ruta_entrega"] is not None:
            saltos = len(resultado["ruta_entrega"]) - 1
            ruta_texto = " → ".join(resultado["ruta_entrega"])
        else:
            saltos = None
            ruta_texto = "No se encontró ruta de entrega"

        registro = {
            "hora": paquete["hora"],
            "id": paquete["id"],
            "tipo": paquete["tipo"],
            "prioridad": paquete["prioridad"],
            "origen": paquete["origen"],
            "destino": paquete["destino"],
            "ttl": paquete["ttl"],
            "estado": "Entregado" if resultado["entregado"] else "No entregado",
            "saltos": saltos if saltos is not None else "-",
            "transmisiones": resultado["transmisiones"],
            "duplicados_descartados": resultado["duplicados_descartados"],
            "ruta": ruta_texto
        }

        st.session_state.historial.append(registro)


# ============================================================
# RESULTADOS Y VISUALIZACIÓN
# ============================================================

st.divider()

resultado = st.session_state.ultimo_resultado
paquete = st.session_state.ultimo_paquete

col_estado, col_grafico = st.columns([0.9, 1.6])

with col_estado:
    st.subheader("Estado del último envío")

    if resultado is None or paquete is None:
        st.markdown(
            """
            <div class="status-info">
            Todavía no se ha enviado ninguna alerta SOS.
            Selecciona el tipo de emergencia y presiona <b>ENVIAR SOS</b>.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        if resultado["entregado"]:
            st.markdown(
                """
                <div class="status-ok">
                <b>Alerta entregada.</b><br>
                El mensaje logró llegar al nodo destino.
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div class="status-bad">
                <b>Alerta no entregada.</b><br>
                La red no logró alcanzar el nodo destino con el TTL y fallos actuales.
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("### Paquete generado")

        st.code(
            f"""
ID: {paquete['id']}
Tipo: {paquete['tipo']}
Prioridad: {paquete['prioridad']}
Origen: {paquete['origen']}
Destino: {paquete['destino']}
TTL inicial: {paquete['ttl']}
Hora: {paquete['hora']}
Mensaje: {paquete['mensaje']}
            """,
            language="text"
        )

        if resultado["ruta_entrega"] is not None:
            ruta = resultado["ruta_entrega"]
            saltos = len(ruta) - 1
            st.write("### Ruta de entrega")
            st.code(" → ".join(ruta), language="text")
        else:
            saltos = 0
            st.write("### Ruta de entrega")
            st.code("No entregado", language="text")

        m1, m2 = st.columns(2)
        m1.metric("Saltos", saltos)
        m2.metric("Transmisiones", resultado["transmisiones"])

        m3, m4 = st.columns(2)
        m3.metric("Duplicados descartados", resultado["duplicados_descartados"])
        m4.metric("Descartes por TTL", resultado["descartes_ttl"])

with col_grafico:
    st.subheader("Visualización técnica de la red")

    dibujar_red(
        G,
        resultado=resultado,
        nodos_caidos=nodos_caidos,
        origen=paquete["origen"] if paquete else origen,
        destino=paquete["destino"] if paquete else destino
    )


# ============================================================
# LOG DE EVENTOS
# ============================================================

st.divider()
st.subheader("Registro de eventos de la propagación")

if resultado is not None:
    df_logs = pd.DataFrame(resultado["logs"])
    st.dataframe(df_logs, use_container_width=True)
else:
    st.info("Cuando envíes un SOS, aquí aparecerá el paso a paso de la propagación.")


# ============================================================
# HISTORIAL DE MENSAJES
# ============================================================

st.divider()
st.subheader("Historial de alertas")

if st.session_state.historial:
    df_historial = pd.DataFrame(st.session_state.historial)

    df_historial["orden_prioridad"] = df_historial["prioridad"].map(PRIORIDAD_VALOR)
    df_historial = df_historial.sort_values(
        by=["orden_prioridad", "hora"],
        ascending=[True, False]
    ).drop(columns=["orden_prioridad"])

    st.dataframe(df_historial, use_container_width=True)

    csv = df_historial.to_csv(index=False).encode("utf-8")

    col_descargar, col_limpiar = st.columns([1, 1])

    with col_descargar:
        st.download_button(
            label="Descargar historial CSV",
            data=csv,
            file_name="historial_alertas_sos.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_limpiar:
        if st.button("Limpiar historial", use_container_width=True):
            st.session_state.historial = []
            st.session_state.ultimo_resultado = None
            st.session_state.ultimo_paquete = None
            st.rerun()
else:
    st.info("Aún no hay alertas registradas.")


# ============================================================
# EXPLICACIÓN TÉCNICA PARA LA DEMO
# ============================================================

st.divider()

with st.expander("Explicación técnica del prototipo"):
    st.write(
        """
        Este prototipo representa una red LoRa/ad hoc de emergencia en la que cada nodo puede actuar como emisor,
        receptor y reenviador de paquetes. La aplicación genera un paquete SOS con un identificador único,
        prioridad, TTL y mensaje de emergencia.

        La propagación se realiza mediante flooding controlado. Esto significa que cada nodo reenvía el paquete
        a sus vecinos únicamente si no lo ha recibido antes y si el TTL aún permite más saltos. Cuando un nodo
        recibe un paquete repetido, lo descarta usando el ID del mensaje. De esta forma se evita que el mismo
        mensaje circule indefinidamente por la red.

        Los escenarios de nodos caídos permiten evaluar la tolerancia a fallos. Si un nodo intermedio deja de
        funcionar, la red intenta propagar la alerta por otros caminos disponibles. El historial permite comparar
        diferentes pruebas según prioridad, cantidad de saltos, transmisiones y duplicados descartados.
        """
    )
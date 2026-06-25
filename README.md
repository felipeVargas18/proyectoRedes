# Proyecto Redes - App SOS Rural con Red LoRa/Ad Hoc Simulada

## Descripción

Este proyecto propone un prototipo de comunicación de emergencia para comunidades rurales o zonas geográficamente aisladas, donde la infraestructura tradicional de telecomunicaciones puede ser limitada, inexistente o fallar durante una emergencia.

El sistema está compuesto por dos partes principales:

1. **Aplicación SOS Rural** desarrollada en Flutter.
2. **Simulador de red LoRa/ad hoc** desarrollado en Python con Streamlit.

La aplicación móvil permite generar un paquete de emergencia tipo SOS, mientras que el simulador representa cómo ese paquete se propaga en una red multi-salto formada por nodos que actúan como emisores, receptores y reenviadores de información.

## Objetivo del proyecto

Diseñar y validar conceptualmente una arquitectura de comunicación ad hoc para gestión de emergencias en comunidades rurales, usando mecanismos de:

* Comunicación multi-salto.
* Priorización de mensajes.
* Control de duplicados.
* TTL, Time To Live.
* Tolerancia a fallos.
* Simulación de red LoRa/ad hoc.

## Arquitectura general

```text
Usuario
  ↓
App SOS Rural
  ↓
Paquete JSON de emergencia
  ↓
Simulador de red LoRa/ad hoc
  ↓
Propagación multi-salto
  ↓
Centro de ayuda / brigadista / puesto médico
```

La aplicación representa la capa de usuario. El simulador representa la capa de red.

En una implementación física futura, la aplicación podría conectarse a un módulo LoRa externo, por ejemplo un ESP32 LoRa, mediante Bluetooth, WiFi local o conexión serial.

## Componentes del proyecto

### 1. Aplicación Flutter

Ubicación:

```text
sos_rural_app/
```

La app permite:

* Seleccionar nodo origen.
* Seleccionar nodo destino.
* Escoger tipo de emergencia.
* Asignar prioridad.
* Escribir un mensaje.
* Configurar TTL.
* Generar un paquete SOS en formato JSON.
* Copiar el paquete generado.

Ejemplo de paquete generado:

```json
{
  "id": "SOS-784320",
  "origen": "N1 - Usuario comunidad",
  "destino": "N8 - Centro de ayuda",
  "tipo": "Emergencia médica",
  "prioridad": "Alta",
  "mensaje": "Se requiere atención médica urgente.",
  "ttl": 5,
  "hora": "14:42:22",
  "tecnologia": "LoRa ad hoc simulada",
  "estado": "Paquete generado"
}
```

### 2. Simulador Streamlit

Archivo principal:

```text
app.py
```

El simulador permite:

* Visualizar una red ad hoc con nodos.
* Enviar paquetes SOS.
* Simular nodos caídos.
* Evaluar rutas multi-salto.
* Aplicar TTL.
* Descartar mensajes duplicados.
* Registrar eventos de propagación.
* Mostrar historial de alertas.
* Exportar resultados en CSV.

## Topología simulada

La red simulada está compuesta por ocho nodos:

```text
N1 - Usuario comunidad
N2 - Casa rural
N3 - Escuela
N4 - Puesto médico
N5 - Repetidor cerro
N6 - Brigadista
N7 - Vereda norte
N8 - Centro de ayuda
```

Cada nodo representa un posible dispositivo de comunicación ubicado en un punto estratégico de una comunidad rural.

## Tecnologías utilizadas

### Simulador

* Python
* Streamlit
* NetworkX
* Matplotlib
* Pandas

### Aplicación móvil

* Flutter
* Dart

## Instalación del simulador

Desde la carpeta principal del proyecto, instalar las dependencias:

```bash
pip install streamlit networkx matplotlib pandas
```

Ejecutar el simulador:

```bash
python -m streamlit run app.py
```

La aplicación se abrirá en el navegador en:

```text
http://localhost:8501
```

## Instalación de la app Flutter

Entrar a la carpeta de la aplicación:

```bash
cd sos_rural_app
```

Ejecutar en Chrome:

```bash
flutter run -d chrome
```

Para ejecutar en Android se requiere tener instalado Android Studio y el Android SDK.

## Pruebas realizadas

Se realizaron pruebas sobre diferentes escenarios:

1. **Escenario sin fallos:** la alerta se entrega correctamente desde el usuario hasta el centro de ayuda.
2. **TTL reducido:** el mensaje no se entrega cuando el TTL no permite alcanzar el destino.
3. **Nodo intermedio caído:** la red intenta propagar el mensaje por caminos alternativos.
4. **Control de duplicados:** los nodos descartan mensajes que ya habían recibido previamente.
5. **Historial de alertas:** el sistema registra prioridad, estado, saltos, transmisiones y duplicados descartados.

## Resultado esperado

En un escenario normal, una alerta de emergencia médica enviada desde:

```text
N1 - Usuario comunidad
```

hacia:

```text
N8 - Centro de ayuda
```

puede seguir una ruta como:

```text
N1 → N2 → N5 → N8
```

Esto demuestra el funcionamiento multi-salto de la red.

## Limitaciones

Este prototipo no implementa comunicación LoRa física real. La red LoRa/ad hoc se modela mediante simulación.

No se evalúan todavía:

* Alcance real de radiofrecuencia.
* Interferencias.
* Pérdidas de señal.
* Consumo energético.
* Comunicación directa con módulos ESP32 LoRa.
* Pruebas de campo.

## Trabajo futuro

Como trabajo futuro se propone:

* Implementar nodos físicos con ESP32 LoRa.
* Conectar la app móvil con un módulo LoRa externo.
* Realizar pruebas de alcance en campo.
* Incorporar geolocalización.
* Evaluar consumo energético.
* Mejorar el algoritmo de propagación usando calidad de enlace, batería o congestión.
* Integrar almacenamiento de eventos y alertas.

## Autor

Luis Felipe Vargas Bernal
Universidad Nacional de Colombia
Curso: Redes de Computadores

## Estado del proyecto

Prototipo funcional académico.

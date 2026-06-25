import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  runApp(const SosRuralApp());
}

class SosRuralApp extends StatelessWidget {
  const SosRuralApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SOS Rural',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.red,
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      home: const SosHomePage(),
    );
  }
}

class SosHomePage extends StatefulWidget {
  const SosHomePage({super.key});

  @override
  State<SosHomePage> createState() => _SosHomePageState();
}

class _SosHomePageState extends State<SosHomePage> {
  final TextEditingController _mensajeController = TextEditingController();

  final List<String> nodos = [
    'N1 - Usuario comunidad',
    'N2 - Casa rural',
    'N3 - Escuela',
    'N4 - Puesto médico',
    'N5 - Repetidor cerro',
    'N6 - Brigadista',
    'N7 - Vereda norte',
    'N8 - Centro de ayuda',
  ];

  final Map<String, Map<String, String>> emergencias = {
    'Emergencia médica': {
      'prioridad': 'Alta',
      'mensaje': 'Se requiere atención médica urgente.',
    },
    'Incendio': {
      'prioridad': 'Alta',
      'mensaje': 'Se reporta incendio en la zona.',
    },
    'Inundación': {
      'prioridad': 'Alta',
      'mensaje': 'Se requiere apoyo por inundación.',
    },
    'Persona desaparecida': {
      'prioridad': 'Media',
      'mensaje': 'Se reporta una persona desaparecida.',
    },
    'Vía bloqueada': {
      'prioridad': 'Media',
      'mensaje': 'Se reporta una vía bloqueada.',
    },
    'Solicitud de alimentos/agua': {
      'prioridad': 'Baja',
      'mensaje': 'Se solicita apoyo con alimentos o agua.',
    },
  };

  String origen = 'N1 - Usuario comunidad';
  String destino = 'N8 - Centro de ayuda';
  String tipoEmergencia = 'Emergencia médica';
  String prioridad = 'Alta';
  double ttl = 5;

  Map<String, dynamic>? paqueteGenerado;

  @override
  void initState() {
    super.initState();
    _mensajeController.text = emergencias[tipoEmergencia]!['mensaje']!;
  }

  @override
  void dispose() {
    _mensajeController.dispose();
    super.dispose();
  }

  String generarIdSos() {
    final random = Random();
    final numero = random.nextInt(999999).toString().padLeft(6, '0');
    return 'SOS-$numero';
  }

  String horaActual() {
    final now = DateTime.now();
    final h = now.hour.toString().padLeft(2, '0');
    final m = now.minute.toString().padLeft(2, '0');
    final s = now.second.toString().padLeft(2, '0');
    return '$h:$m:$s';
  }

  void actualizarEmergencia(String nuevaEmergencia) {
    setState(() {
      tipoEmergencia = nuevaEmergencia;
      prioridad = emergencias[nuevaEmergencia]!['prioridad']!;
      _mensajeController.text = emergencias[nuevaEmergencia]!['mensaje']!;
    });
  }

  void enviarSos() {
    final paquete = {
      'id': generarIdSos(),
      'origen': origen,
      'destino': destino,
      'tipo': tipoEmergencia,
      'prioridad': prioridad,
      'mensaje': _mensajeController.text,
      'ttl': ttl.round(),
      'hora': horaActual(),
      'tecnologia': 'LoRa ad hoc simulada',
      'estado': 'Paquete generado',
    };

    setState(() {
      paqueteGenerado = paquete;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Alerta SOS generada correctamente'),
        backgroundColor: Colors.red,
      ),
    );
  }

  String paqueteComoJson() {
    if (paqueteGenerado == null) return '';
    const encoder = JsonEncoder.withIndent('  ');
    return encoder.convert(paqueteGenerado);
  }

  Future<void> copiarJson() async {
    if (paqueteGenerado == null) return;

    await Clipboard.setData(
      ClipboardData(text: paqueteComoJson()),
    );

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Paquete copiado al portapapeles'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final jsonPaquete = paqueteComoJson();

    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      appBar: AppBar(
        title: const Text('SOS Rural'),
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(18),
          child: Column(
            children: [
              _buildPhoneCard(),
              const SizedBox(height: 18),
              if (paqueteGenerado != null) _buildResultadoCard(jsonPaquete),
              const SizedBox(height: 18),
              _buildDescripcionTecnica(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPhoneCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: Colors.black87, width: 2),
        boxShadow: const [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 12,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        children: [
          const Icon(
            Icons.warning_amber_rounded,
            color: Colors.red,
            size: 54,
          ),
          const SizedBox(height: 6),
          const Text(
            'App SOS Rural',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Generación de alertas para red LoRa/ad hoc',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.black54),
          ),
          const SizedBox(height: 22),

          _buildDropdown(
            label: 'Ubicación / nodo del usuario',
            value: origen,
            items: nodos,
            onChanged: (value) {
              if (value == null) return;
              setState(() {
                origen = value;
              });
            },
          ),

          const SizedBox(height: 14),

          _buildDropdown(
            label: 'Nodo destino',
            value: destino,
            items: nodos,
            onChanged: (value) {
              if (value == null) return;
              setState(() {
                destino = value;
              });
            },
          ),

          const SizedBox(height: 14),

          _buildDropdown(
            label: 'Tipo de emergencia',
            value: tipoEmergencia,
            items: emergencias.keys.toList(),
            onChanged: (value) {
              if (value == null) return;
              actualizarEmergencia(value);
            },
          ),

          const SizedBox(height: 14),

          _buildDropdown(
            label: 'Prioridad del mensaje',
            value: prioridad,
            items: const ['Alta', 'Media', 'Baja'],
            onChanged: (value) {
              if (value == null) return;
              setState(() {
                prioridad = value;
              });
            },
          ),

          const SizedBox(height: 14),

          TextField(
            controller: _mensajeController,
            maxLines: 3,
            decoration: InputDecoration(
              labelText: 'Mensaje',
              filled: true,
              fillColor: const Color(0xFFF1F3F4),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
          ),

          const SizedBox(height: 18),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'TTL máximo de saltos',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              Text(
                ttl.round().toString(),
                style: const TextStyle(
                  color: Colors.red,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          Slider(
            value: ttl,
            min: 1,
            max: 8,
            divisions: 7,
            activeColor: Colors.red,
            label: ttl.round().toString(),
            onChanged: (value) {
              setState(() {
                ttl = value;
              });
            },
          ),

          const SizedBox(height: 12),

          SizedBox(
            width: double.infinity,
            height: 56,
            child: FilledButton.icon(
              onPressed: origen == destino ? null : enviarSos,
              icon: const Icon(Icons.sos),
              label: const Text(
                'ENVIAR SOS',
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                ),
              ),
              style: FilledButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
                disabledBackgroundColor: Colors.grey,
              ),
            ),
          ),

          if (origen == destino) ...[
            const SizedBox(height: 10),
            const Text(
              'El origen y el destino no pueden ser el mismo nodo.',
              style: TextStyle(color: Colors.red),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildResultadoCard(String jsonPaquete) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F5E9),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.green.shade700),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.check_circle, color: Colors.green),
              SizedBox(width: 8),
              Text(
                'Paquete SOS generado',
                style: TextStyle(
                  fontSize: 19,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'ID: ${paqueteGenerado!['id']}',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          Text('Tipo: ${paqueteGenerado!['tipo']}'),
          Text('Prioridad: ${paqueteGenerado!['prioridad']}'),
          Text('Origen: ${paqueteGenerado!['origen']}'),
          Text('Destino: ${paqueteGenerado!['destino']}'),
          Text('TTL: ${paqueteGenerado!['ttl']}'),
          Text('Hora: ${paqueteGenerado!['hora']}'),

          const SizedBox(height: 16),

          const Text(
            'Formato del paquete generado:',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),

          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.black87,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              jsonPaquete,
              style: const TextStyle(
                color: Colors.white,
                fontFamily: 'monospace',
                fontSize: 12,
              ),
            ),
          ),

          const SizedBox(height: 12),

          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: copiarJson,
              icon: const Icon(Icons.copy),
              label: const Text('Copiar paquete JSON'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDescripcionTecnica() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFE3F2FD),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.blue.shade700),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Rol de esta app en el proyecto',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Esta aplicación representa la capa de usuario del sistema. '
            'Cuando una persona presiona el botón SOS, se genera un paquete '
            'con ID, origen, destino, prioridad, TTL, tipo de emergencia y mensaje. '
            'Ese paquete es el que posteriormente se propaga en la red LoRa/ad hoc simulada.',
          ),
        ],
      ),
    );
  }

  Widget _buildDropdown({
    required String label,
    required String value,
    required List<String> items,
    required ValueChanged<String?> onChanged,
  }) {
    return DropdownButtonFormField<String>(
      value: value,
      isExpanded: true,
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: const Color(0xFFF1F3F4),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
      items: items.map((item) {
        return DropdownMenuItem<String>(
          value: item,
          child: Text(
            item,
            overflow: TextOverflow.ellipsis,
          ),
        );
      }).toList(),
      onChanged: onChanged,
    );
  }
}
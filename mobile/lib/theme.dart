import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Direction artistique éditoriale (magazine), volontairement à l'écart de
/// l'esthétique « IA générique » : fond charbon chaud, serif de titrage
/// (Fraunces), accent ambré, teintes par catégorie.
class AppTheme {
  static const ink = Color(0xFFF7F3EC);
  static const muted = Color(0xFFC9C1B3);
  static const bg = Color(0xFF0C0B0A);
  static const accent = Color(0xFFE0A367);

  static const categoryColors = <String, Color>{
    'science': Color(0xFF3B6EA5),
    'nature': Color(0xFF4A7C59),
    'histoire': Color(0xFF9A6A3C),
    'psychologie': Color(0xFF7D5BA6),
    'geopolitique': Color(0xFFA8503F),
    'economie': Color(0xFF3F7D78),
    'espace': Color(0xFF2D3561),
    'tech': Color(0xFF4A5568),
    'sante': Color(0xFF3E7C6A),
    'culture': Color(0xFF8A5A7A),
  };

  static const categoryGlyphs = <String, String>{
    'science': '🌅', 'nature': '🐜', 'histoire': '🏛️', 'psychologie': '💭',
    'geopolitique': '🌍', 'economie': '📈', 'espace': '🪐', 'tech': '⚙️',
    'sante': '🧬', 'culture': '🎭',
  };

  static Color colorFor(String cat) => categoryColors[cat] ?? const Color(0xFF5A4A3A);
  static String glyphFor(String cat) => categoryGlyphs[cat] ?? '✨';

  static TextStyle serif(double size, {FontWeight weight = FontWeight.w800, Color? color}) =>
      GoogleFonts.fraunces(fontSize: size, fontWeight: weight, height: 1.1, color: color ?? ink);

  static ThemeData build() {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: bg,
      colorScheme: base.colorScheme.copyWith(primary: accent, surface: bg),
      textTheme: GoogleFonts.interTextTheme(base.textTheme).apply(
        bodyColor: ink,
        displayColor: ink,
      ),
    );
  }
}

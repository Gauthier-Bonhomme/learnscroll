import 'dart:io' show Platform;

/// URL de base de l'API LearnScroll.
///
/// - Émulateur Android : `10.0.2.2` pointe vers le `localhost` de la machine hôte.
/// - iOS / desktop / web : `localhost`.
/// Passe une valeur en dur ou via --dart-define=API_BASE=... pour un vrai serveur.
class Config {
  static const _override = String.fromEnvironment('API_BASE', defaultValue: '');

  static String get apiBase {
    if (_override.isNotEmpty) return _override;
    try {
      if (Platform.isAndroid) return 'http://10.0.2.2:8077';
    } catch (_) {
      // Platform indisponible (web) -> localhost.
    }
    return 'http://localhost:8077';
  }
}

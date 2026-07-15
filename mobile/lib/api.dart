import 'dart:convert';
import 'package:http/http.dart' as http;

import 'config.dart';
import 'models.dart';

/// Client de l'API LearnScroll. Le feed ne lit que du contenu déjà généré ;
/// aucune génération IA n'est déclenchée côté client (sauf l'approfondissement
/// 'pourquoi' à la demande, qui est mis en cache serveur).
class Api {
  final String userId;
  final String _base = Config.apiBase;

  Api(this.userId);

  Future<List<CardSummary>> feed({int limit = 12}) async {
    final r = await http.get(Uri.parse('$_base/api/feed?user_id=$userId&limit=$limit'));
    final data = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    return (data['cards'] as List)
        .map((e) => CardSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CardDetail> detail(int id) async {
    final r = await http.get(Uri.parse('$_base/api/cards/$id'));
    return CardDetail.fromJson(jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>);
  }

  Future<List<CardSummary>> favorites() async {
    final r = await http.get(Uri.parse('$_base/api/favorites?user_id=$userId'));
    final data = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    return (data['cards'] as List)
        .map((e) => CardSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Profile> profile() async {
    final r = await http.get(Uri.parse('$_base/api/profile?user_id=$userId'));
    return Profile.fromJson(jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>);
  }

  Future<WhyLayer> deepen(int cardId, String question) async {
    final r = await http.post(
      Uri.parse('$_base/api/cards/$cardId/why'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'question': question}),
    );
    final j = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    return WhyLayer(j['question'] ?? question, j['answer'] ?? '');
  }

  Future<void> interact(int cardId, String kind, {int dwellMs = 0}) async {
    await http.post(
      Uri.parse('$_base/api/interactions'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': userId,
        'card_id': cardId,
        'kind': kind,
        'dwell_ms': dwellMs,
      }),
    );
  }
}

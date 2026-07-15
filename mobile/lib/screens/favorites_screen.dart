import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';
import 'detail_screen.dart';

class FavoritesScreen extends StatefulWidget {
  final Api api;
  const FavoritesScreen({super.key, required this.api});

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  late Future<List<CardSummary>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.api.favorites();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: AppTheme.bg,
        title: Text('Favoris', style: AppTheme.serif(22)),
      ),
      body: RefreshIndicator(
        color: AppTheme.accent,
        onRefresh: () async => setState(() => _future = widget.api.favorites()),
        child: FutureBuilder<List<CardSummary>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator(color: AppTheme.accent));
            }
            final cards = snap.data!;
            if (cards.isEmpty) {
              return ListView(children: const [
                SizedBox(height: 120),
                Center(child: Text('Aucun favori pour le moment.',
                    style: TextStyle(color: AppTheme.muted))),
              ]);
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: cards.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (_, i) => _tile(context, cards[i]),
            );
          },
        ),
      ),
    );
  }

  Widget _tile(BuildContext context, CardSummary c) => InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => DetailScreen(api: widget.api, cardId: c.id),
        )),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.colorFor(c.category).withValues(alpha: .28),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: Colors.white12),
          ),
          child: Row(children: [
            Text(AppTheme.glyphFor(c.category), style: const TextStyle(fontSize: 30)),
            const SizedBox(width: 14),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(c.hook, style: AppTheme.serif(17, weight: FontWeight.w600)),
                const SizedBox(height: 4),
                Text('${c.category} · ⏱ ${c.readingTime}',
                    style: const TextStyle(color: AppTheme.muted, fontSize: 13)),
              ]),
            ),
          ]),
        ),
      );
}

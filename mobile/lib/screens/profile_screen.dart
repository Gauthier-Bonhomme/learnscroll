import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';

class ProfileScreen extends StatefulWidget {
  final Api api;
  const ProfileScreen({super.key, required this.api});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late Future<Profile> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.api.profile();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: AppTheme.bg,
        title: Text('Ton parcours', style: AppTheme.serif(22)),
      ),
      body: RefreshIndicator(
        color: AppTheme.accent,
        onRefresh: () async => setState(() => _future = widget.api.profile()),
        child: FutureBuilder<Profile>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator(color: AppTheme.accent));
            }
            final p = snap.data!;
            return ListView(
              padding: const EdgeInsets.all(20),
              children: [
                _streakBanner(p),
                const SizedBox(height: 20),
                Row(children: [
                  Expanded(child: _stat('${p.cardsViewed}', 'cartes lues')),
                  const SizedBox(width: 12),
                  Expanded(child: _stat('${p.learningMinutes}', 'min d\'apprentissage')),
                ]),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(child: _stat('${p.favorites}', 'favoris')),
                  const SizedBox(width: 12),
                  Expanded(child: _stat('${p.seriesCompleted.length}', 'séries complétées')),
                ]),
                const SizedBox(height: 24),
                if (p.seriesCompleted.isNotEmpty) ...[
                  const Text('SÉRIES COMPLÉTÉES',
                      style: TextStyle(color: AppTheme.muted, fontSize: 13, letterSpacing: 1)),
                  const SizedBox(height: 10),
                  for (final s in p.seriesCompleted)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Text('🏅 $s', style: const TextStyle(fontSize: 16)),
                    ),
                ],
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _streakBanner(Profile p) => Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFF3A2A17), Color(0xFF1A1610)]),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppTheme.accent.withValues(alpha: .35)),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Text('🔥 ${p.streak}', style: AppTheme.serif(34, color: AppTheme.accent)),
            const SizedBox(width: 10),
            const Padding(
              padding: EdgeInsets.only(bottom: 6),
              child: Text('jours de série', style: TextStyle(color: AppTheme.muted)),
            ),
          ]),
          const SizedBox(height: 6),
          Text('Niveau : ${p.level.name}',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        ]),
      );

  Widget _stat(String value, String label) => Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: const Color(0xFF17150F),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white12),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(value, style: AppTheme.serif(28)),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(color: AppTheme.muted, fontSize: 13)),
        ]),
      );
}

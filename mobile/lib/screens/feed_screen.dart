import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';
import 'detail_screen.dart';

class FeedScreen extends StatefulWidget {
  final Api api;
  const FeedScreen({super.key, required this.api});

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  final _controller = PageController();
  List<CardSummary> _cards = [];
  bool _loading = true;
  int _current = 0;
  DateTime _enteredAt = DateTime.now();
  final Set<int> _faved = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final cards = await widget.api.feed();
      setState(() {
        _cards = cards;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  /// Journalise la vue + le temps passé sur la carte quittée.
  void _onPageChanged(int index) {
    if (_cards.isNotEmpty) {
      final left = _cards[_current];
      final dwell = DateTime.now().difference(_enteredAt).inMilliseconds;
      if (dwell > 1200) widget.api.interact(left.id, 'view', dwellMs: dwell);
    }
    _enteredAt = DateTime.now();
    _current = index;
    if (index >= _cards.length - 2) _loadMore();
  }

  Future<void> _loadMore() async {
    final more = await widget.api.feed();
    final existing = _cards.map((c) => c.id).toSet();
    final fresh = more.where((c) => !existing.contains(c.id)).toList();
    if (fresh.isNotEmpty) setState(() => _cards.addAll(fresh));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.accent));
    }
    if (_cards.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(28),
          child: Text(
            "Feed vide.\nLance le backend puis « python seed_samples.py ».",
            textAlign: TextAlign.center,
            style: TextStyle(color: AppTheme.muted, height: 1.5),
          ),
        ),
      );
    }
    return PageView.builder(
      scrollDirection: Axis.vertical,
      controller: _controller,
      onPageChanged: _onPageChanged,
      itemCount: _cards.length,
      itemBuilder: (_, i) => _CardTile(
        card: _cards[i],
        faved: _faved.contains(_cards[i].id),
        onFav: () => _toggleFav(_cards[i]),
        onShare: () => _share(_cards[i]),
        onDiscover: () => _open(_cards[i]),
      ),
    );
  }

  void _toggleFav(CardSummary c) {
    final on = _faved.contains(c.id);
    setState(() => on ? _faved.remove(c.id) : _faved.add(c.id));
    if (!on) widget.api.interact(c.id, 'favorite');
    _snack(on ? 'Retiré des favoris' : 'Ajouté aux favoris ❤️');
  }

  void _share(CardSummary c) {
    widget.api.interact(c.id, 'share');
    _snack('Partage 📤');
  }

  void _open(CardSummary c) {
    widget.api.interact(c.id, 'expand');
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => DetailScreen(api: widget.api, cardId: c.id),
    ));
  }

  void _snack(String m) => ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(m), duration: const Duration(milliseconds: 1200)),
      );

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

class _CardTile extends StatelessWidget {
  final CardSummary card;
  final bool faved;
  final VoidCallback onFav, onShare, onDiscover;

  const _CardTile({
    required this.card,
    required this.faved,
    required this.onFav,
    required this.onShare,
    required this.onDiscover,
  });

  @override
  Widget build(BuildContext context) {
    final tone = AppTheme.colorFor(card.category);
    return GestureDetector(
      onTap: onDiscover,
      child: Container(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0, -0.7),
            radius: 1.1,
            colors: [tone, AppTheme.bg],
          ),
        ),
        child: Stack(
          children: [
            Positioned(
              top: 90,
              left: 0,
              right: 0,
              child: Center(
                child: Text(AppTheme.glyphFor(card.category),
                    style: const TextStyle(fontSize: 110, color: Colors.white24)),
              ),
            ),
            const Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Colors.transparent, Colors.transparent, Color(0xE60C0B0A)],
                    stops: [0, .45, 1],
                  ),
                ),
              ),
            ),
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(22, 0, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Wrap(spacing: 8, children: [
                      _chip(card.category),
                      _chip('⏱ ${card.readingTime}', accent: true),
                      if (card.mode == 'actualite') _chip('actu'),
                    ]),
                    const SizedBox(height: 14),
                    Text(card.hook, style: AppTheme.serif(32)),
                    const SizedBox(height: 12),
                    Text(card.teaser,
                        style: const TextStyle(fontSize: 16, color: AppTheme.muted, height: 1.5)),
                    const SizedBox(height: 22),
                    Row(children: [
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: onDiscover,
                          icon: const Text('👇'),
                          label: const Text('Découvrir'),
                          style: FilledButton.styleFrom(
                            backgroundColor: AppTheme.accent,
                            foregroundColor: const Color(0xFF221507),
                            padding: const EdgeInsets.symmetric(vertical: 15),
                            textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      _action(faved ? '❤️' : '🤍', onFav, active: faved),
                      const SizedBox(width: 10),
                      _action('📤', onShare),
                    ]),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _chip(String label, {bool accent = false}) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 5),
        decoration: BoxDecoration(
          color: Colors.black26,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: accent ? AppTheme.accent.withValues(alpha: .5) : Colors.white24),
        ),
        child: Text(label,
            style: TextStyle(fontSize: 12, color: accent ? AppTheme.accent : AppTheme.ink)),
      );

  Widget _action(String glyph, VoidCallback onTap, {bool active = false}) => InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(
            color: active ? AppTheme.accent : Colors.black26,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: active ? AppTheme.accent : Colors.white24),
          ),
          child: Center(child: Text(glyph, style: const TextStyle(fontSize: 20))),
        ),
      );
}

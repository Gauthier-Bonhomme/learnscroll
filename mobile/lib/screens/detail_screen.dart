import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';

class DetailScreen extends StatefulWidget {
  final Api api;
  final int cardId;
  const DetailScreen({super.key, required this.api, required this.cardId});

  @override
  State<DetailScreen> createState() => _DetailScreenState();
}

class _DetailScreenState extends State<DetailScreen> {
  CardDetail? _card;
  bool _whyOpen = false;
  final List<WhyLayer> _extra = []; // couches générées à la demande
  final _controller = TextEditingController();
  bool _deepening = false;

  @override
  void initState() {
    super.initState();
    widget.api.detail(widget.cardId).then((c) => setState(() => _card = c));
  }

  Future<void> _deepen() async {
    final q = _controller.text.trim();
    if (q.isEmpty || _deepening) return;
    setState(() => _deepening = true);
    final layer = await widget.api.deepen(widget.cardId, q);
    setState(() {
      _extra.add(layer);
      _controller.clear();
      _deepening = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = _card;
    return Scaffold(
      appBar: AppBar(
        backgroundColor: AppTheme.bg,
        leading: const BackButton(),
        title: Text(c?.category ?? '', style: const TextStyle(fontSize: 15, color: AppTheme.muted)),
      ),
      body: c == null
          ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : ListView(
              padding: const EdgeInsets.fromLTRB(22, 8, 22, 60),
              children: [
                Wrap(spacing: 8, children: [
                  _chip('⏱ ${c.readingTime}', accent: true),
                  if (c.series != null) _chip('${c.series} · ${c.seriesIndex ?? ''}'),
                ]),
                const SizedBox(height: 14),
                Text(c.hook, style: AppTheme.serif(28)),
                const SizedBox(height: 18),
                ..._paragraphs(c.body),
                const SizedBox(height: 20),
                if (!_whyOpen)
                  OutlinedButton(
                    onPressed: () => setState(() => _whyOpen = true),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.accent,
                      side: const BorderSide(color: AppTheme.accent),
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      minimumSize: const Size.fromHeight(0),
                    ),
                    child: const Text("💡 J'ai compris… mais pourquoi ?",
                        style: TextStyle(fontWeight: FontWeight.w600)),
                  ),
                if (_whyOpen) ..._whyTree(c),
                const SizedBox(height: 30),
                if (c.sources.isNotEmpty) _sources(c),
              ],
            ),
    );
  }

  List<Widget> _paragraphs(String body) => body
      .split('\n')
      .where((p) => p.trim().isNotEmpty)
      .map((p) => Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Text(p, style: const TextStyle(fontSize: 17, height: 1.65, color: Color(0xFFECE6DB))),
          ))
      .toList();

  List<Widget> _whyTree(CardDetail c) {
    final layers = [...c.whyLayers, ..._extra];
    return [
      for (final l in layers) _layer(l),
      Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(children: [
          Expanded(
            child: TextField(
              controller: _controller,
              style: const TextStyle(color: AppTheme.ink),
              onSubmitted: (_) => _deepen(),
              decoration: InputDecoration(
                hintText: 'Creuser encore : pose ta question…',
                hintStyle: const TextStyle(color: AppTheme.muted),
                filled: true,
                fillColor: const Color(0xFF17150F),
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              ),
            ),
          ),
          const SizedBox(width: 8),
          FilledButton(
            onPressed: _deepening ? null : _deepen,
            style: FilledButton.styleFrom(
                backgroundColor: AppTheme.accent, foregroundColor: const Color(0xFF221507)),
            child: _deepening
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Creuser'),
          ),
        ]),
      ),
    ];
  }

  Widget _layer(WhyLayer l) => Container(
        margin: const EdgeInsets.symmetric(vertical: 12),
        padding: const EdgeInsets.only(left: 16),
        decoration: const BoxDecoration(
          border: Border(left: BorderSide(color: AppTheme.accent, width: 2)),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(l.question, style: AppTheme.serif(18, weight: FontWeight.w600)),
          const SizedBox(height: 6),
          Text(l.answer, style: const TextStyle(color: Color(0xFFDED7CA), height: 1.55)),
        ]),
      );

  Widget _sources(CardDetail c) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Divider(color: Colors.white24),
          const SizedBox(height: 8),
          const Text('SOURCES',
              style: TextStyle(color: AppTheme.muted, fontSize: 13, letterSpacing: 1)),
          const SizedBox(height: 8),
          for (final s in c.sources)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Text('↗ ${s.title}', style: const TextStyle(color: AppTheme.accent)),
            ),
        ],
      );

  Widget _chip(String label, {bool accent = false}) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 5),
        decoration: BoxDecoration(
          color: Colors.black26,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: accent ? AppTheme.accent : Colors.white24),
        ),
        child: Text(label,
            style: TextStyle(fontSize: 12, color: accent ? AppTheme.accent : AppTheme.ink)),
      );

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

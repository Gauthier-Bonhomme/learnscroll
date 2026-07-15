import 'dart:math';
import 'package:flutter/material.dart';

import 'api.dart';
import 'screens/feed_screen.dart';
import 'screens/favorites_screen.dart';
import 'screens/profile_screen.dart';
import 'theme.dart';

void main() => runApp(const LearnScrollApp());

/// Identifiant utilisateur local anonyme (à remplacer par un vrai auth plus tard).
String _makeUserId() =>
    'u${Random().nextInt(1 << 32).toRadixString(36)}';

class LearnScrollApp extends StatelessWidget {
  const LearnScrollApp({super.key});

  @override
  Widget build(BuildContext context) {
    final api = Api(_makeUserId());
    return MaterialApp(
      title: 'LearnScroll',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.build(),
      home: HomeShell(api: api),
    );
  }
}

class HomeShell extends StatefulWidget {
  final Api api;
  const HomeShell({super.key, required this.api});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      FeedScreen(api: widget.api),
      FavoritesScreen(api: widget.api),
      ProfileScreen(api: widget.api),
    ];
    return Scaffold(
      body: IndexedStack(index: _tab, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        backgroundColor: const Color(0xFF15130F),
        indicatorColor: AppTheme.accent.withValues(alpha: .25),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.bolt_outlined), selectedIcon: Icon(Icons.bolt), label: 'Feed'),
          NavigationDestination(icon: Icon(Icons.favorite_border), selectedIcon: Icon(Icons.favorite), label: 'Favoris'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profil'),
        ],
      ),
    );
  }
}

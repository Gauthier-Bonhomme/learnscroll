class CardSummary {
  final int id;
  final String hook, category, mode, readingTime, teaser, imageUrl;
  final List<String> tags;

  CardSummary({
    required this.id,
    required this.hook,
    required this.category,
    required this.mode,
    required this.readingTime,
    required this.teaser,
    required this.imageUrl,
    required this.tags,
  });

  factory CardSummary.fromJson(Map<String, dynamic> j) => CardSummary(
        id: j['id'] as int,
        hook: j['hook'] ?? '',
        category: j['category'] ?? '',
        mode: j['mode'] ?? 'info',
        readingTime: j['reading_time'] ?? '',
        teaser: j['teaser'] ?? '',
        imageUrl: j['image_url'] ?? '',
        tags: (j['tags'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      );
}

class WhyLayer {
  final String question, answer;
  WhyLayer(this.question, this.answer);
  factory WhyLayer.fromJson(Map<String, dynamic> j) =>
      WhyLayer(j['question'] ?? '', j['answer'] ?? '');
}

class Source {
  final String title, url;
  Source(this.title, this.url);
  factory Source.fromJson(Map<String, dynamic> j) =>
      Source(j['title'] ?? '', j['url'] ?? '');
}

class CardDetail extends CardSummary {
  final String body;
  final List<WhyLayer> whyLayers;
  final List<Source> sources;
  final String? series;
  final int? seriesIndex;

  CardDetail({
    required super.id,
    required super.hook,
    required super.category,
    required super.mode,
    required super.readingTime,
    required super.teaser,
    required super.imageUrl,
    required super.tags,
    required this.body,
    required this.whyLayers,
    required this.sources,
    this.series,
    this.seriesIndex,
  });

  factory CardDetail.fromJson(Map<String, dynamic> j) => CardDetail(
        id: j['id'] as int,
        hook: j['hook'] ?? '',
        category: j['category'] ?? '',
        mode: j['mode'] ?? 'info',
        readingTime: j['reading_time'] ?? '',
        teaser: j['teaser'] ?? '',
        imageUrl: j['image_url'] ?? '',
        tags: (j['tags'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        body: j['body'] ?? '',
        whyLayers: (j['why_layers'] as List? ?? [])
            .map((e) => WhyLayer.fromJson(e as Map<String, dynamic>))
            .toList(),
        sources: (j['sources'] as List? ?? [])
            .map((e) => Source.fromJson(e as Map<String, dynamic>))
            .toList(),
        series: j['series'] as String?,
        seriesIndex: j['series_index'] as int?,
      );
}

class Level {
  final String name;
  final int views;
  Level(this.name, this.views);
  factory Level.fromJson(Map<String, dynamic> j) =>
      Level(j['name'] ?? 'Curieux', j['views'] ?? 0);
}

class Profile {
  final int streak;
  final Level level;
  final int cardsViewed, favorites;
  final double learningMinutes;
  final List<String> seriesCompleted;

  Profile({
    required this.streak,
    required this.level,
    required this.cardsViewed,
    required this.favorites,
    required this.learningMinutes,
    required this.seriesCompleted,
  });

  factory Profile.fromJson(Map<String, dynamic> j) {
    final stats = (j['stats'] ?? {}) as Map<String, dynamic>;
    return Profile(
      streak: j['streak'] ?? 0,
      level: Level.fromJson((j['level'] ?? {}) as Map<String, dynamic>),
      cardsViewed: stats['cards_viewed'] ?? 0,
      favorites: stats['favorites'] ?? 0,
      learningMinutes: (stats['learning_minutes'] ?? 0).toDouble(),
      seriesCompleted: (stats['series_completed'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
    );
  }
}

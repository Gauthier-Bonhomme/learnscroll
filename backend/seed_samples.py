"""
Insère quelques cartes de démonstration écrites à la main (aucun appel API).
Sert à voir tourner le backend et le feed avant d'avoir lancé un vrai batch.

    python seed_samples.py
"""

from __future__ import annotations

from app.db import Card, SessionLocal, Series, init_db

SAMPLES = [
    dict(
        external_id="demo-ciel-rouge", category="science", mode="info", reading_time="30s",
        hook="Pourquoi le ciel devient-il rouge au coucher du soleil ?",
        teaser="Un simple filtre de lumière qui raconte un voyage de 150 millions de km.",
        body="Le soir, la lumière du Soleil ne vous arrive plus de face : elle rase "
             "l'atmosphère et traverse bien plus d'air qu'à midi. En route, le bleu est "
             "dispersé dans tous les sens et se perd. Ne survivent que les rouges et les "
             "oranges, assez robustes pour aller au bout du trajet. Ce coucher de soleil "
             "flamboyant, c'est littéralement la lumière fatiguée du voyage.",
        why=[{"question": "Pourquoi le bleu se disperse-t-il plus que le rouge ?",
              "answer": "Parce qu'il a une longueur d'onde plus courte : il ricoche sur les "
                        "molécules d'air bien plus facilement, comme une petite vague brisée "
                        "par le moindre obstacle."},
             {"question": "Pourquoi ça traverse plus d'air le soir ?",
              "answer": "Le Soleil est bas sur l'horizon : ses rayons entrent en biais et "
                        "parcourent une tranche d'atmosphère beaucoup plus épaisse qu'à la "
                        "verticale de midi."}],
        sources=[{"title": "NASA Science", "url": "https://science.nasa.gov"}],
        tags=["lumière", "atmosphère", "optique"],
        image_prompt="editorial wide photo of a deep red sunset over the sea, natural light",
    ),
    dict(
        external_id="demo-fourmis", category="nature", mode="info", reading_time="2min",
        hook="Comment une fourmilière décide sans aucun chef ?",
        teaser="Des milliers d'individus, zéro patron, et pourtant des choix quasi optimaux.",
        body="Aucune fourmi ne 'commande'. Chacune suit des règles minuscules : suivre une "
             "piste odorante, la renforcer si elle mène à de la nourriture, l'ignorer sinon. "
             "Multipliez ça par dix mille et un comportement collectif intelligent émerge : "
             "la colonie trouve le chemin le plus court sans qu'aucune fourmi ne l'ait "
             "calculé. C'est l'intelligence en essaim — la même idée qui inspire aujourd'hui "
             "des algorithmes de routage et de logistique.",
        why=[{"question": "Pourquoi le chemin le plus court finit par gagner ?",
              "answer": "Il est parcouru plus vite, donc plus souvent : sa piste odorante est "
                        "rechargée en permanence pendant que les détours s'évaporent."}],
        sources=[{"title": "CNRS Le Journal", "url": "https://lejournal.cnrs.fr"}],
        tags=["fourmis", "intelligence collective", "biologie"],
        image_prompt="macro editorial photo of ants on a trail, shallow depth of field",
    ),
    dict(
        external_id="demo-reves", category="psychologie", mode="info", reading_time="30s",
        hook="Pourquoi oublie-t-on ses rêves en quelques minutes ?",
        teaser="Votre cerveau les vit intensément… puis refuse presque de les archiver.",
        body="Au réveil, un rêve peut sembler inoubliable — et s'effacer avant le café. En "
             "cause : pendant le sommeil paradoxal, les zones du cerveau qui fabriquent des "
             "souvenirs durables tournent au ralenti. Le rêve est vécu mais mal 'enregistré'. "
             "Si vous ne le rejouez pas mentalement dans les premières secondes, il glisse. "
             "D'où l'astuce des carnets de rêves posés sur la table de nuit.",
        why=[{"question": "Pourquoi la mémoire tourne-t-elle au ralenti la nuit ?",
              "answer": "Le cerveau consacre le sommeil à trier et consolider la journée "
                        "écoulée, pas à mémoriser de nouveaux scénarios en direct."}],
        sources=[{"title": "Inserm", "url": "https://www.inserm.fr"}],
        tags=["rêves", "mémoire", "sommeil"],
        image_prompt="dreamy editorial photo of a blurred bedroom at dawn, soft light",
    ),
    dict(
        external_id="demo-rome-1", category="histoire", mode="info", reading_time="2min",
        hook="Rome a-t-elle vraiment été fondée par deux frères élevés par une louve ?",
        teaser="Entre le mythe de Romulus et ce que l'archéologie a réellement déterré.",
        body="Le mythe est splendide : Romulus et Rémus, jumeaux abandonnés, sauvés par une "
             "louve, fondateurs d'une ville sur le Palatin. L'archéologie, elle, raconte une "
             "histoire moins héroïque mais tout aussi fascinante : des cabanes de bergers "
             "regroupées sur des collines, un carrefour commercial bien placé sur le Tibre, "
             "et des siècles de fusion entre peuples. Rome n'est pas née d'un coup de génie "
             "— elle a poussé, village après village.",
        why=[{"question": "Pourquoi ce site précis sur le Tibre ?",
              "answer": "Un gué franchissable, sept collines défendables et une route du sel "
                        "qui passait juste là : la géographie a fait le reste."}],
        sources=[{"title": "British Museum", "url": "https://www.britishmuseum.org"}],
        tags=["Rome", "antiquité", "archéologie"],
        image_prompt="editorial photo of the Roman Palatine hill ruins at golden hour",
        series="Les Romains", series_index=1,
    ),
    dict(
        external_id="demo-ormuz", category="geopolitique", mode="info", reading_time="5min",
        hook="Pourquoi un détroit de 30 km fait trembler l'économie mondiale ?",
        teaser="Le détroit d'Ormuz : le goulot par lequel passe un cinquième du pétrole.",
        body="Regardez une carte du Golfe : tout le pétrole de la région doit se faufiler "
             "par une passe étroite entre l'Iran et Oman, le détroit d'Ormuz. Environ un "
             "cinquième de la consommation mondiale de pétrole y transite chaque jour. La "
             "moindre tension — une menace de blocage, un incident naval — et les marchés "
             "s'affolent, car il n'existe aucun contournement rapide. Un point minuscule sur "
             "la carte, un levier géant sur les prix.",
        why=[{"question": "Pourquoi ne pas simplement contourner le détroit ?",
              "answer": "Quelques oléoducs existent, mais leur capacité est très inférieure "
                        "au trafic maritime : ils ne peuvent absorber qu'une fraction du flux."}],
        sources=[{"title": "Reuters", "url": "https://www.reuters.com"}],
        tags=["pétrole", "Ormuz", "commerce", "énergie"],
        image_prompt="editorial aerial photo of oil tankers in a narrow strait, dusk",
    ),
]


def run() -> None:
    init_db()
    s = SessionLocal()
    added = 0
    for item in SAMPLES:
        if s.query(Card).filter_by(external_id=item["external_id"]).first():
            continue
        series = None
        if item.get("series"):
            series = s.query(Series).filter_by(name=item["series"]).one_or_none()
            if not series:
                series = Series(name=item["series"], category=item["category"])
                s.add(series)
                s.flush()
        card = Card(
            external_id=item["external_id"], hook=item["hook"], category=item["category"],
            mode=item["mode"], reading_time=item["reading_time"], teaser=item["teaser"],
            body=item["body"], image_prompt=item["image_prompt"], model_used="demo-seed",
            series=series, series_index=item.get("series_index"),
        )
        card.why_layers = item["why"]
        card.sources = item["sources"]
        card.tags = item["tags"]
        s.add(card)
        added += 1
    s.commit()
    total = s.query(Card).count()
    s.close()
    print(f"✔ {added} cartes de démo ajoutées. Total en base : {total}.")


if __name__ == "__main__":
    run()

"""
Insère quelques cartes de démonstration écrites à la main (aucun appel API)
dans le catalogue. Sert à voir tourner le site avant d'avoir lancé un vrai batch.

    python seed_samples.py
    python export_site.py
"""

from __future__ import annotations

import catalog

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
        why_layers=[
            {"question": "Pourquoi le bleu se disperse-t-il plus que le rouge ?",
             "answer": "Parce qu'il a une longueur d'onde plus courte : il ricoche sur les "
                       "molécules d'air bien plus facilement, comme une petite vague brisée "
                       "par le moindre obstacle."},
            {"question": "Pourquoi ça traverse plus d'air le soir ?",
             "answer": "Le Soleil est bas sur l'horizon : ses rayons entrent en biais et "
                       "parcourent une tranche d'atmosphère beaucoup plus épaisse qu'à la "
                       "verticale de midi."},
            {"question": "Pourquoi l'atmosphère ne disperse-t-elle pas toutes les couleurs pareil ?",
             "answer": "La diffusion de Rayleigh dépend violemment de la longueur d'onde : "
                       "diviser la longueur d'onde par deux multiplie la diffusion par seize. "
                       "Le ciel entier est une démonstration de physique en temps réel."},
        ],
        sources=[{"title": "NASA Science", "url": "https://science.nasa.gov"}],
        tags=["lumière", "atmosphère", "optique"],
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
        why_layers=[
            {"question": "Pourquoi le chemin le plus court finit par gagner ?",
             "answer": "Il est parcouru plus vite, donc plus souvent : sa piste odorante est "
                       "rechargée en permanence pendant que les détours s'évaporent."},
            {"question": "Pourquoi personne n'a besoin de voir la carte en entier ?",
             "answer": "Chaque fourmi ne lit que l'information locale — l'odeur sous ses "
                       "pattes. La 'carte' n'existe nulle part : elle émerge de millions de "
                       "micro-décisions qui se corrigent mutuellement."},
        ],
        sources=[{"title": "CNRS Le Journal", "url": "https://lejournal.cnrs.fr"}],
        tags=["fourmis", "intelligence collective", "biologie"],
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
        why_layers=[
            {"question": "Pourquoi la mémoire tourne-t-elle au ralenti la nuit ?",
             "answer": "Le cerveau consacre le sommeil à trier et consolider la journée "
                       "écoulée, pas à mémoriser de nouveaux scénarios en direct."},
            {"question": "Pourquoi certains rêves restent-ils quand même ?",
             "answer": "Ceux du petit matin, faits juste avant le réveil, bénéficient d'un "
                       "cerveau déjà en train de redémarrer : la machine à souvenirs se "
                       "rallume pendant que le film tourne encore."},
        ],
        sources=[{"title": "Inserm", "url": "https://www.inserm.fr"}],
        tags=["rêves", "mémoire", "sommeil"],
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
        why_layers=[
            {"question": "Pourquoi ce site précis sur le Tibre ?",
             "answer": "Un gué franchissable, sept collines défendables et une route du sel "
                       "qui passait juste là : la géographie a fait le reste."},
            {"question": "Pourquoi le mythe de la louve a-t-il tenu deux mille ans ?",
             "answer": "Parce que Rome en avait besoin : une origine divine et sauvage "
                       "justifiait sa domination. Les empires écrivent toujours leur légende "
                       "après coup — et la nôtre continue de les croire."},
        ],
        sources=[{"title": "British Museum", "url": "https://www.britishmuseum.org"}],
        tags=["Rome", "antiquité", "archéologie"],
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
        why_layers=[
            {"question": "Pourquoi ne pas simplement contourner le détroit ?",
             "answer": "Quelques oléoducs existent, mais leur capacité est très inférieure "
                       "au trafic maritime : ils ne peuvent absorber qu'une fraction du flux."},
            {"question": "Pourquoi personne ne construit plus d'oléoducs, alors ?",
             "answer": "Un oléoduc traverse des frontières, des déserts et des décennies de "
                       "géopolitique. Le bateau, lui, ne demande la permission à personne — "
                       "tant que le détroit reste ouvert."},
        ],
        sources=[{"title": "Reuters", "url": "https://www.reuters.com"}],
        tags=["pétrole", "Ormuz", "commerce", "énergie"],
    ),
]


def run() -> None:
    conn = catalog.connect()
    added = sum(1 for item in SAMPLES if catalog.upsert_card(conn, item))
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    conn.close()
    print(f"✔ {added} cartes de démo ajoutées. Total au catalogue : {total}.")


if __name__ == "__main__":
    run()

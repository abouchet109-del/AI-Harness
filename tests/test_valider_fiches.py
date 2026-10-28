import json
import re
import shutil
from pathlib import Path

import pytest

from scripts.valider_fiches import (
    ErreurFormat,
    ErreurSchema,
    charger_schema,
    charger_tags,
    lire_frontmatter,
    main,
    valider_coffre,
)

SCHEMA_DE_TEST = Path(__file__).parent / "fixtures" / "_schema.json"
VRAI_COFFRE = Path("D:/Europa/5. Memoire IA")

TAGS = """# Vocabulaire
- `statut/actif` — en cours
- `statut/idee` — pas commencé
- `projet/demo` — projet de test
- `domaine/code` — code
- `domaine/etudes` — études
- `cours/maths` — cours de test
- `type/presentation` — diaporama
"""

PROJET = """---
fiche: projet
resume: Un projet de démonstration.
tags: [statut/actif, projet/demo, domaine/code]
sources: ["D:/Projets/demo"]
depot: D:/Projets/demo
maj: 2026-10-28
---
# demo
"""

NOTION = """---
fiche: notion
resume: Les suites géométriques.
tags:
  - cours/maths
  - domaine/etudes
sources:
  - poly chapitre 3
maitrise: 2
revise_le: 2026-10-27
maj: 2026-10-28
---
"""

TRAVAIL = """---
fiche: travail
resume: Exposé de groupe.
tags: [statut/actif, cours/maths, type/presentation]
sources: [consigne du prof]
echeance: 2026-11-15
documents: []
maj: 2026-10-28
---
"""

INBOX = """---
fiche: inbox
titre: Exercice fait
date: 2026-10-28T14:30
origine: manuel
provenance: interne
sources: [session 123]
cible: "[[suites]]"
tags_proposes: [type/nouveau]
a_valider: false
---
- Exercice 3 réussi.
"""


def creer_coffre(tmp_path, fichiers):
    (tmp_path / "_TAGS.md").write_text(TAGS, encoding="utf-8")
    shutil.copy(SCHEMA_DE_TEST, tmp_path / "_schema.json")
    for chemin, contenu in fichiers.items():
        cible = tmp_path / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")
    return tmp_path


def erreurs_de(tmp_path, fichiers):
    return [message for _, message in valider_coffre(creer_coffre(tmp_path, fichiers))]


def test_frontmatter_listes_en_ligne_et_en_bloc():
    meta = lire_frontmatter(NOTION)
    assert meta["tags"] == ["cours/maths", "domaine/etudes"]
    assert meta["maitrise"] == "2"
    assert lire_frontmatter(INBOX)["cible"] == "[[suites]]"
    assert lire_frontmatter(PROJET)["sources"] == ["D:/Projets/demo"]


def test_frontmatter_absent_refuse():
    with pytest.raises(ErreurFormat):
        lire_frontmatter("# Pas de frontmatter\n")


def test_charger_tags(tmp_path):
    (tmp_path / "_TAGS.md").write_text(TAGS, encoding="utf-8")
    assert "cours/maths" in charger_tags(tmp_path / "_TAGS.md")


def test_coffre_valide(tmp_path):
    assert erreurs_de(tmp_path, {
        "Projets/demo/demo.md": PROJET,
        "Etudes/maths/notions/suites.md": NOTION,
        "Etudes/maths/travaux/expose.md": TRAVAIL,
        "00-Inbox/2026-10-28-1430-manuel-exo.md": INBOX,
        "_gabarits/projet.md": "---\nfiche: projet\nresume: \n---\n",
        "Journal/2026-10-28.md": "# Journal\n",
    }) == []


def test_champ_obligatoire_manquant(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Projets/demo/demo.md": PROJET.replace("resume: Un projet de démonstration.\n", "")})
    assert any("resume" in e for e in erreurs)


def test_tag_inconnu(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Projets/demo/demo.md": PROJET.replace("domaine/code", "langage/cobol")})
    assert any("langage/cobol" in e for e in erreurs)


def test_sources_vides(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Projets/demo/demo.md": PROJET.replace('["D:/Projets/demo"]', "[]")})
    assert any("sources" in e for e in erreurs)


def test_depot_vide_autorise_pour_une_idee(tmp_path):
    idee = PROJET.replace("statut/actif", "statut/idee").replace("depot: D:/Projets/demo", "depot: ")
    assert erreurs_de(tmp_path, {"Projets/demo/demo.md": idee}) == []
    actif = PROJET.replace("depot: D:/Projets/demo", "depot: ")
    assert any("depot" in e for e in erreurs_de(tmp_path, {"Projets/demo/demo.md": actif}))


def test_deux_statuts_refuses(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Projets/demo/demo.md": PROJET.replace("statut/actif,", "statut/actif, statut/idee,")})
    assert any("statut/" in e for e in erreurs)


def test_maitrise_hors_echelle(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Etudes/maths/notions/suites.md": NOTION.replace("maitrise: 2", "maitrise: 7")})
    assert any("maitrise" in e for e in erreurs)


def test_date_invalide(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Etudes/maths/travaux/expose.md": TRAVAIL.replace("2026-11-15", "15/11/2026")})
    assert any("echeance" in e for e in erreurs)


def test_fiche_mal_rangee(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Connaissances/suites.md": NOTION})
    assert any("emplacement" in e for e in erreurs)


def test_tag_projet_different_du_dossier(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Etudes/physique/notions/suites.md": NOTION})
    assert any("cours/physique" in e for e in erreurs)


def test_inbox_externe_doit_etre_a_valider(tmp_path):
    externe = INBOX.replace("provenance: interne", "provenance: externe")
    assert any("a_valider" in e for e in erreurs_de(tmp_path, {"00-Inbox/note.md": externe}))
    assert erreurs_de(tmp_path, {"00-Inbox/note.md": externe.replace("a_valider: false", "a_valider: true")}) == []


def test_noms_de_fichier_en_double(tmp_path):
    erreurs = erreurs_de(tmp_path, {
        "Etudes/maths/notions/suites.md": NOTION,
        "Connaissances/suites.md": NOTION.replace("fiche: notion", "fiche: connaissance"),
    })
    assert any("nom de fichier" in e for e in erreurs)


def test_fiche_de_type_inconnu(tmp_path):
    erreurs = erreurs_de(tmp_path, {"Connaissances/x.md": "---\nfiche: recette\n---\n"})
    assert any("recette" in e for e in erreurs)


def schema_modifie(tmp_path, modifier):
    """Écrit dans tmp_path un coffre dont le schéma de test a été modifié par `modifier`."""
    coffre = creer_coffre(tmp_path, {})
    schema = json.loads(SCHEMA_DE_TEST.read_text(encoding="utf-8"))
    modifier(schema)
    (coffre / "_schema.json").write_text(json.dumps(schema), encoding="utf-8")
    return coffre


def test_type_ajoute_dans_le_schema_sans_toucher_au_code(tmp_path):
    def ajouter_recette(schema):
        schema["types"]["recette"] = {
            "emplacement": r"Cuisine/[^/]+\.md",
            "champs_communs": True,
            "obligatoires": ["difficulte"],
            "valeurs": {"difficulte": ["facile", "difficile"]},
        }

    coffre = schema_modifie(tmp_path, ajouter_recette)
    recette = """---
fiche: recette
resume: Des crêpes.
tags: [domaine/code]
sources: [grand-mère]
maj: 2026-10-28
difficulte: facile
---
"""
    (coffre / "Cuisine").mkdir()
    (coffre / "Cuisine" / "crepes.md").write_text(recette, encoding="utf-8")
    assert valider_coffre(coffre) == []
    (coffre / "Cuisine" / "crepes.md").write_text(recette.replace("facile", "moyen"), encoding="utf-8")
    assert any("difficulte" in message for _, message in valider_coffre(coffre))


def test_schema_absent(tmp_path):
    coffre = creer_coffre(tmp_path, {})
    (coffre / "_schema.json").unlink()
    with pytest.raises(ErreurSchema, match="introuvable"):
        valider_coffre(coffre)
    assert main([str(coffre)]) == 2


def test_schema_json_invalide(tmp_path):
    coffre = creer_coffre(tmp_path, {})
    (coffre / "_schema.json").write_text("{ pas du json", encoding="utf-8")
    with pytest.raises(ErreurSchema, match="JSON"):
        valider_coffre(coffre)
    assert main([str(coffre)]) == 2


@pytest.mark.parametrize("modifier, attendu", [
    (lambda s: s["types"]["projet"].pop("emplacement"), "emplacement"),
    (lambda s: s["types"]["projet"].update(emplacement="Projets/(["), "emplacement invalide"),
    (lambda s: s["types"]["projet"].update(obligatoires="depot"), "liste de textes"),
    (lambda s: s["types"]["projet"].update(facettes_unique=["statut"]), "clé inconnue"),
    (lambda s: s["types"]["connaissance"].update(facette_du_slug="projet"), "slug"),
    (lambda s: s["types"]["inbox"]["si"][0].pop("message"), "règle si"),
    (lambda s: s.update(types={}), "types"),
    (lambda s: s.update(version="deux"), "version"),
])
def test_schema_mal_decrit(tmp_path, modifier, attendu):
    coffre = schema_modifie(tmp_path, modifier)
    with pytest.raises(ErreurSchema, match=attendu):
        valider_coffre(coffre)
    assert main([str(coffre)]) == 2


@pytest.mark.skipif(not VRAI_COFFRE.is_dir(), reason="coffre réel absent")
def test_types_de_formats_md_et_du_schema_identiques():
    schema = charger_schema(VRAI_COFFRE / "_schema.json")
    formats = (VRAI_COFFRE / "_FORMATS.md").read_text(encoding="utf-8")
    types_documentes = set(re.findall(r"^\| ([a-z]+) \| ", formats, flags=re.MULTILINE)) - {"fiche"}
    assert types_documentes == set(schema["types"])


@pytest.mark.skipif(not VRAI_COFFRE.is_dir(), reason="coffre réel absent")
def test_vrai_coffre_valide():
    assert valider_coffre(VRAI_COFFRE) == []

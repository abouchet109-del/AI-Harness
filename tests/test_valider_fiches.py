import pytest

from scripts.valider_fiches import (
    ErreurFormat,
    charger_tags,
    lire_frontmatter,
    valider_coffre,
)

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

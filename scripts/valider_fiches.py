"""Vérifie que les fiches du coffre mémoire respectent `_FORMATS.md`.

Usage : python scripts/valider_fiches.py "D:/Europa/5. Memoire IA"
Sortie : une ligne par erreur, code 1 s'il y en a, 0 sinon.
"""

import re
import sys
from datetime import date, datetime
from pathlib import Path

DOSSIERS_IGNORES = {"_gabarits", "Journal", "Veille"}
FICHIERS_RACINE_IGNORES = {"_INDEX.md", "_TAGS.md", "_FORMATS.md"}
CHAMPS_LISTE = {"tags", "sources", "documents", "tags_proposes"}
CHAMPS_COMMUNS = ["resume", "tags", "sources", "maj"]

# fiche -> (motif d'emplacement, champs obligatoires, facettes à exactement une valeur)
REGLES = {
    "projet": (r"Projets/(?P<slug>[^/]+)/(?P=slug)\.md", CHAMPS_COMMUNS + ["depot"], ["statut", "projet"]),
    "composant": (r"Projets/(?P<slug>[^/]+)/composants/[^/]+\.md", CHAMPS_COMMUNS + ["chemin"], ["projet"]),
    "connaissance": (r"Connaissances/[^/]+\.md", CHAMPS_COMMUNS, []),
    "cours": (r"Etudes/(?P<slug>[^/]+)/(?P=slug)\.md", CHAMPS_COMMUNS + ["echeance"], ["statut", "cours"]),
    "notion": (r"Etudes/(?P<slug>[^/]+)/notions/[^/]+\.md", CHAMPS_COMMUNS + ["maitrise", "revise_le"], ["cours"]),
    "travail": (r"Etudes/(?P<slug>[^/]+)/travaux/[^/]+\.md", CHAMPS_COMMUNS + ["echeance", "documents"], ["statut", "cours"]),
    "inbox": (r"00-Inbox/[^/]+\.md", ["titre", "date", "origine", "provenance", "sources", "a_valider"], []),
}
# Facette dont la valeur doit être le slug du dossier.
FACETTE_DU_SLUG = {"projet": "projet", "composant": "projet", "cours": "cours", "notion": "cours", "travail": "cours"}


class ErreurFormat(ValueError):
    pass


def lire_frontmatter(texte):
    """Lit le sous-ensemble de YAML autorisé : `cle: valeur`, `cle: [a, b]`, ou `cle:` suivi de lignes `- a`."""
    lignes = texte.splitlines()
    if not lignes or lignes[0].strip() != "---":
        raise ErreurFormat("pas de frontmatter (la première ligne doit être ---)")
    try:
        fin = lignes.index("---", 1)
    except ValueError:
        raise ErreurFormat("frontmatter non fermé (--- manquant)") from None
    meta = {}
    cle_en_cours = None
    for numero, ligne in enumerate(lignes[1:fin], start=2):
        if not ligne.strip():
            continue
        element = re.fullmatch(r"\s+- (.*)", ligne)
        if element and cle_en_cours:
            if not isinstance(meta[cle_en_cours], list):
                meta[cle_en_cours] = []
            meta[cle_en_cours].append(_sans_guillemets(element.group(1).strip()))
            continue
        champ = re.fullmatch(r"([a-z_]+):(.*)", ligne)
        if not champ:
            raise ErreurFormat(f"ligne {numero} illisible : {ligne!r}")
        cle, valeur = champ.group(1), champ.group(2).strip()
        if cle in meta:
            raise ErreurFormat(f"champ {cle} en double")
        meta[cle] = _lire_valeur(valeur)
        cle_en_cours = cle if valeur == "" else None
    return meta


def _lire_valeur(valeur):
    if valeur.startswith("[") and not valeur.startswith("[["):
        if not valeur.endswith("]"):
            raise ErreurFormat(f"liste non fermée : {valeur!r}")
        interieur = valeur[1:-1].strip()
        return [_sans_guillemets(v.strip()) for v in interieur.split(",")] if interieur else []
    return _sans_guillemets(valeur)


def _sans_guillemets(valeur):
    if len(valeur) >= 2 and valeur[0] == valeur[-1] and valeur[0] in "\"'":
        return valeur[1:-1]
    return valeur


def charger_tags(chemin_tags):
    texte = chemin_tags.read_text(encoding="utf-8")
    return set(re.findall(r"^- `([a-z0-9-]+/[a-z0-9-]+)`", texte, flags=re.MULTILINE))


def valider_fiche(meta, chemin_relatif, tags_autorises):
    """Renvoie la liste des erreurs d'une fiche dont le frontmatter est déjà lu."""
    fiche = meta.get("fiche")
    if fiche not in REGLES:
        return [f"fiche inconnue : {fiche!r} (attendu : {', '.join(REGLES)})"]
    motif, obligatoires, facettes_uniques = REGLES[fiche]
    erreurs = [f"champ obligatoire absent : {champ}" for champ in obligatoires if champ not in meta]
    for champ in CHAMPS_LISTE & meta.keys():
        if isinstance(meta[champ], str):
            meta[champ] = [meta[champ]] if meta[champ] else []

    emplacement = re.fullmatch(motif, chemin_relatif)
    if not emplacement:
        erreurs.append(f"emplacement incorrect pour une fiche {fiche} (attendu : {motif})")

    if "resume" in meta and not meta["resume"]:
        erreurs.append("resume vide")
    if "sources" in meta and not meta["sources"]:
        erreurs.append("sources vide : chaque fiche garde un lien vers sa source")
    erreurs += _verifier_dates(meta)

    tags = meta.get("tags", [])
    erreurs += [f"tag absent de _TAGS.md : {tag}" for tag in tags if tag not in tags_autorises]
    for facette in facettes_uniques:
        nombre = sum(tag.startswith(facette + "/") for tag in tags)
        if nombre != 1:
            erreurs.append(f"il faut exactement un tag {facette}/ (trouvé : {nombre})")
    if emplacement and fiche in FACETTE_DU_SLUG:
        attendu = f"{FACETTE_DU_SLUG[fiche]}/{emplacement.group('slug')}"
        if attendu not in tags:
            erreurs.append(f"tag {attendu} attendu d'après le dossier")

    if fiche == "projet" and "statut/idee" not in tags and not meta.get("depot"):
        erreurs.append("depot vide : autorisé seulement pour statut/idee")
    if fiche == "composant" and not meta.get("chemin"):
        erreurs.append("chemin vide : la fiche composant pointe vers le code")
    if fiche == "travail" and not any(tag.startswith("type/") for tag in tags):
        erreurs.append("il faut au moins un tag type/ (presentation, devoir...)")
    if fiche == "notion" and meta.get("maitrise") not in {"0", "1", "2", "3", "4"}:
        erreurs.append(f"maitrise doit valoir 0, 1, 2, 3 ou 4 (trouvé : {meta.get('maitrise')!r})")
    if fiche == "inbox":
        erreurs += _verifier_inbox(meta)
    return erreurs


def _verifier_dates(meta):
    erreurs = []
    for champ, vide_permis in [("maj", False), ("echeance", meta.get("fiche") == "cours"), ("revise_le", True)]:
        if champ not in meta or (vide_permis and meta[champ] == ""):
            continue
        try:
            date.fromisoformat(meta[champ])
        except (TypeError, ValueError):
            erreurs.append(f"{champ} doit être une date AAAA-MM-JJ (trouvé : {meta[champ]!r})")
    return erreurs


def _verifier_inbox(meta):
    erreurs = []
    try:
        datetime.strptime(meta.get("date", ""), "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        erreurs.append(f"date doit être AAAA-MM-JJTHH:MM (trouvé : {meta.get('date')!r})")
    if not meta.get("titre"):
        erreurs.append("titre vide")
    if not meta.get("origine"):
        erreurs.append("origine vide")
    if meta.get("provenance") not in {"interne", "externe"}:
        erreurs.append("provenance doit valoir interne ou externe")
    if meta.get("a_valider") not in {"true", "false"}:
        erreurs.append("a_valider doit valoir true ou false")
    if meta.get("provenance") == "externe" and meta.get("a_valider") != "true":
        erreurs.append("contenu externe : a_valider doit valoir true")
    return erreurs


def fiches_du_coffre(racine):
    for chemin in sorted(racine.rglob("*.md")):
        relatif = chemin.relative_to(racine)
        if relatif.parts[0] in DOSSIERS_IGNORES or relatif.parts[0].startswith("."):
            continue
        if len(relatif.parts) == 1 and relatif.name in FICHIERS_RACINE_IGNORES:
            continue
        yield chemin, relatif.as_posix()


def valider_coffre(racine):
    """Renvoie la liste des (chemin relatif, message) pour tout le coffre."""
    racine = Path(racine)
    tags_autorises = charger_tags(racine / "_TAGS.md")
    erreurs = []
    vus = {}
    for chemin, relatif in fiches_du_coffre(racine):
        if chemin.name in vus:
            erreurs.append((relatif, f"nom de fichier déjà utilisé par {vus[chemin.name]} : un [[lien]] serait ambigu"))
        vus.setdefault(chemin.name, relatif)
        try:
            meta = lire_frontmatter(chemin.read_text(encoding="utf-8"))
        except ErreurFormat as erreur:
            erreurs.append((relatif, str(erreur)))
            continue
        erreurs += [(relatif, message) for message in valider_fiche(meta, relatif, tags_autorises)]
    return erreurs


def main(arguments):
    if len(arguments) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    racine = Path(arguments[0])
    if not (racine / "_TAGS.md").is_file():
        print(f"{racine} : _TAGS.md introuvable, ce n'est pas le coffre mémoire", file=sys.stderr)
        return 2
    erreurs = valider_coffre(racine)
    for relatif, message in erreurs:
        print(f"{relatif} : {message}")
    nombre = sum(1 for _ in fiches_du_coffre(racine))
    print(f"{nombre} fiche(s) lue(s), {len(erreurs)} erreur(s).")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

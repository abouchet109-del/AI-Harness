"""Vérifie que les fiches du coffre mémoire respectent `_schema.json` (décrit dans `_FORMATS.md`).

Usage : python scripts/valider_fiches.py "D:/Europa/5. Memoire IA"
Sortie : une ligne par erreur, code 1 s'il y en a, 0 sinon ; code 2 si le coffre ou son schéma est inutilisable.
"""

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

DOSSIERS_IGNORES = {"_gabarits", "Journal", "Veille"}
FICHIERS_RACINE_IGNORES = {"_INDEX.md", "_TAGS.md", "_FORMATS.md"}

# Clés autorisées au sommet du schéma et dans chaque type : une clé inconnue est une faute de frappe.
CLES_SCHEMA = {"version", "champs_communs", "champs_liste", "non_vides_communs", "dates_communes", "types"}
CLES_TYPE = {
    "emplacement", "champs_communs", "obligatoires", "facettes_uniques", "facettes_au_moins_une",
    "facette_du_slug", "non_vides", "dates", "valeurs", "si",
}
CLES_REGLE_SI = {"champ", "vaut", "alors_champ", "alors_vaut", "message"}


class ErreurFormat(ValueError):
    pass


class ErreurSchema(ValueError):
    pass


def charger_schema(chemin_schema):
    """Lit `_schema.json` et vérifie sa forme ; lève ErreurSchema avec un message clair."""
    try:
        schema = json.loads(chemin_schema.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ErreurSchema(f"{chemin_schema} introuvable") from None
    except json.JSONDecodeError as erreur:
        raise ErreurSchema(f"{chemin_schema.name} n'est pas du JSON valide : {erreur}") from None
    _verifier_schema(schema)
    return schema


def _verifier_schema(schema):
    if not isinstance(schema, dict):
        raise ErreurSchema("_schema.json doit être un objet JSON")
    inconnues = set(schema) - CLES_SCHEMA
    if inconnues:
        raise ErreurSchema(f"clé inconnue dans _schema.json : {', '.join(sorted(inconnues))}")
    version = schema.get("version")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ErreurSchema(f"version du schéma : entier >= 1 attendu (trouvé : {version!r})")
    for cle in ("champs_communs", "champs_liste"):
        _exiger_liste_de_textes(schema.get(cle, []), cle)
    for cle in ("non_vides_communs", "dates_communes"):
        if not isinstance(schema.get(cle, {}), dict):
            raise ErreurSchema(f"{cle} doit être un objet")
    types = schema.get("types")
    if not isinstance(types, dict) or not types:
        raise ErreurSchema("types doit être un objet non vide")
    for nom, decrit in types.items():
        _verifier_type(nom, decrit)


def _exiger_liste_de_textes(valeur, ou):
    if not isinstance(valeur, list) or not all(isinstance(v, str) for v in valeur):
        raise ErreurSchema(f"{ou} doit être une liste de textes")


def _verifier_type(nom, decrit):
    ou = f"type {nom!r}"
    if not isinstance(decrit, dict):
        raise ErreurSchema(f"{ou} : doit être un objet")
    inconnues = set(decrit) - CLES_TYPE
    if inconnues:
        raise ErreurSchema(f"{ou} : clé inconnue : {', '.join(sorted(inconnues))}")
    emplacement = decrit.get("emplacement")
    if not isinstance(emplacement, str):
        raise ErreurSchema(f"{ou} : emplacement (expression régulière) manquant")
    try:
        motif = re.compile(emplacement)
    except re.error as erreur:
        raise ErreurSchema(f"{ou} : emplacement invalide : {erreur}") from None
    for cle in ("obligatoires", "facettes_uniques", "facettes_au_moins_une"):
        _exiger_liste_de_textes(decrit.get(cle, []), f"{ou} : {cle}")
    if "facette_du_slug" in decrit and "slug" not in motif.groupindex:
        raise ErreurSchema(f"{ou} : facette_du_slug demande un groupe (?P<slug>...) dans emplacement")
    for cle in ("non_vides", "dates", "valeurs"):
        if not isinstance(decrit.get(cle, {}), dict):
            raise ErreurSchema(f"{ou} : {cle} doit être un objet")
    for champ, liste in decrit.get("valeurs", {}).items():
        _exiger_liste_de_textes(liste, f"{ou} : valeurs.{champ}")
    regles = decrit.get("si", [])
    if not isinstance(regles, list):
        raise ErreurSchema(f"{ou} : si doit être une liste")
    for regle in regles:
        if not isinstance(regle, dict) or set(regle) != CLES_REGLE_SI:
            raise ErreurSchema(f"{ou} : chaque règle si a exactement les clés {', '.join(sorted(CLES_REGLE_SI))}")


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


def valider_fiche(meta, chemin_relatif, tags_autorises, schema):
    """Renvoie la liste des erreurs d'une fiche dont le frontmatter est déjà lu."""
    fiche = meta.get("fiche")
    types = schema["types"]
    if fiche not in types:
        return [f"fiche inconnue : {fiche!r} (attendu : {', '.join(types)})"]
    regles = types[fiche]
    motif = regles["emplacement"]
    communs = schema.get("champs_communs", []) if regles.get("champs_communs") else []
    erreurs = [f"champ obligatoire absent : {champ}" for champ in communs + regles.get("obligatoires", []) if champ not in meta]
    for champ in set(schema.get("champs_liste", [])) & meta.keys():
        if isinstance(meta[champ], str):
            meta[champ] = [meta[champ]] if meta[champ] else []

    emplacement = re.fullmatch(motif, chemin_relatif)
    if not emplacement:
        erreurs.append(f"emplacement incorrect pour une fiche {fiche} (attendu : {motif})")

    tags = meta.get("tags", [])
    erreurs += _verifier_non_vides({**schema.get("non_vides_communs", {}), **regles.get("non_vides", {})}, meta, tags)
    erreurs += _verifier_dates({**schema.get("dates_communes", {}), **regles.get("dates", {})}, meta)
    erreurs += _verifier_valeurs(regles.get("valeurs", {}), meta)
    erreurs += _verifier_si(regles.get("si", []), meta)

    erreurs += [f"tag absent de _TAGS.md : {tag}" for tag in tags if tag not in tags_autorises]
    for facette in regles.get("facettes_uniques", []):
        nombre = sum(tag.startswith(facette + "/") for tag in tags)
        if nombre != 1:
            erreurs.append(f"il faut exactement un tag {facette}/ (trouvé : {nombre})")
    for facette in regles.get("facettes_au_moins_une", []):
        if not any(tag.startswith(facette + "/") for tag in tags):
            erreurs.append(f"il faut au moins un tag {facette}/")
    facette_du_slug = regles.get("facette_du_slug")
    if emplacement and facette_du_slug:
        attendu = f"{facette_du_slug}/{emplacement.group('slug')}"
        if attendu not in tags:
            erreurs.append(f"tag {attendu} attendu d'après le dossier")
    return erreurs


def _verifier_non_vides(non_vides, meta, tags):
    erreurs = []
    for champ, option in non_vides.items():
        if champ not in meta or meta[champ] or option.get("sauf_si_tag") in tags:
            continue
        precision = option.get("pourquoi") or (f"autorisé seulement pour {option['sauf_si_tag']}" if "sauf_si_tag" in option else "")
        erreurs.append(f"{champ} vide" + (f" : {precision}" if precision else ""))
    return erreurs


def _verifier_dates(dates, meta):
    erreurs = []
    for champ, option in dates.items():
        if champ not in meta or (option.get("vide_permis") and meta[champ] == ""):
            continue
        format_date = option.get("format")
        try:
            if format_date:
                datetime.strptime(meta[champ], format_date)
            else:
                date.fromisoformat(meta[champ])
        except (TypeError, ValueError):
            attendu = option.get("libelle", "AAAA-MM-JJ")
            erreurs.append(f"{champ} doit être une date {attendu} (trouvé : {meta[champ]!r})")
    return erreurs


def _verifier_valeurs(valeurs, meta):
    erreurs = []
    for champ, permises in valeurs.items():
        if champ in meta and meta[champ] not in permises:
            erreurs.append(f"{champ} doit valoir {' ou '.join(permises)} (trouvé : {meta[champ]!r})")
    return erreurs


def _verifier_si(regles_si, meta):
    return [
        regle["message"]
        for regle in regles_si
        if meta.get(regle["champ"]) == regle["vaut"] and meta.get(regle["alors_champ"]) != regle["alors_vaut"]
    ]


def fiches_du_coffre(racine):
    for chemin in sorted(racine.rglob("*.md")):
        relatif = chemin.relative_to(racine)
        if relatif.parts[0] in DOSSIERS_IGNORES or relatif.parts[0].startswith("."):
            continue
        if len(relatif.parts) == 1 and relatif.name in FICHIERS_RACINE_IGNORES:
            continue
        yield chemin, relatif.as_posix()


def valider_coffre(racine):
    """Renvoie la liste des (chemin relatif, message) pour tout le coffre. Lève ErreurSchema si le schéma est inutilisable."""
    racine = Path(racine)
    schema = charger_schema(racine / "_schema.json")
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
        erreurs += [(relatif, message) for message in valider_fiche(meta, relatif, tags_autorises, schema)]
    return erreurs


def main(arguments):
    if len(arguments) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    racine = Path(arguments[0])
    if not (racine / "_TAGS.md").is_file():
        print(f"{racine} : _TAGS.md introuvable, ce n'est pas le coffre mémoire", file=sys.stderr)
        return 2
    try:
        erreurs = valider_coffre(racine)
    except ErreurSchema as erreur:
        print(f"schéma inutilisable : {erreur}", file=sys.stderr)
        return 2
    for relatif, message in erreurs:
        print(f"{relatif} : {message}")
    nombre = sum(1 for _ in fiches_du_coffre(racine))
    print(f"{nombre} fiche(s) lue(s), {len(erreurs)} erreur(s).")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

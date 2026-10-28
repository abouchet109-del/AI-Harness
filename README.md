# AI-Harness

Architecture IA personnelle. Sa brique centrale est une **mémoire de tous mes projets et de ce que j'apprends**, dans un coffre Obsidian, à laquelle d'autres harness se branchent (prof de maths, Anki, veille hackathon…).

## Comment ça marche

- **Lire** : un agent zoome par niveaux, `_INDEX.md` → fiche projet ou cours → fiche composant, notion ou travail → code ou document. Il ne rescanne jamais tout.
- **Écrire** : les sessions et les harness déposent des notes dans `00-Inbox/` ; un seul consolidateur les range dans les fiches, et le code vérifie le résultat.
- **Contrôler** : le coffre est un dépôt git, un point quotidien montre ce qui a changé, tout se corrige dans Obsidian ou par `git revert`.
- **Brancher un nouveau harness** : il respecte le contrat (`_FORMATS.md`, `_schema.json`). S'il apporte une information que la structure ne sait pas stocker, on suit `docs/BRANCHER-UN-HARNESS.md`.

## Où est quoi

| Fichier | Contenu |
|---|---|
| `VISION.md` | La vision, les choix de conception, l'ordre de construction, le modèle et l'effort par étape |
| `docs/ARCHITECTURE.md` | Tous les composants (code, agents, skills, hooks, tâches), comment ça tourne, conformité au guide |
| `docs/FONDEMENTS-MEMOIRE.md` | Ce que les neurosciences, les sciences des organisations et la littérature sur les agents apportent à la conception |
| `evals/` | Les questions posées à la mémoire pour vérifier qu'elle marche |
| `hooks/garde-europa.js` | Hook global qui demande confirmation avant tout accès au coffre perso hors de la mémoire |
| `PROGRESS.md` | Où on en est, prochaine action |
| `docs/DECISIONS.md` | Toutes les décisions, avec leur pourquoi |
| `docs/CONVENTIONS.md` | Façon de travailler : Claude Code, code, agents, principes sourcés |
| `docs/BRANCHER-UN-HARNESS.md` | Procédure pour brancher un harness et faire évoluer la structure |
| `GUIDE-ARCHITECTURE-AGENTIQUE.md` | Guide de référence sur les architectures agentiques |
| `scripts/valider_fiches.py` | Validateur du coffre |
| `CLAUDE.md` | Instructions pour les sessions Claude Code |

Le coffre lui-même est dans `D:\Europa\5. Memoire IA` (dépôt git local à part).

## Commandes

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest
.venv/Scripts/python scripts/valider_fiches.py "D:/Europa/5. Memoire IA"
```

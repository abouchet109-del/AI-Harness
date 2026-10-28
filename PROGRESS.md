# Avancement

## 2026-10-28
- Fait : vision (`VISION.md`), conventions (`CLAUDE.md`, `docs/CONVENTIONS.md`), décisions initiales, dépôt GitHub privé.
- Fait : étape 1. Coffre `D:\Europa\5. Memoire IA` créé (arborescence, `_INDEX.md`, `_TAGS.md`, `_FORMATS.md`, 7 gabarits, git local, pas de dépôt distant). Extension « Études » (cours, notion, travail). Validateur `scripts/valider_fiches.py` + 16 tests pytest verts ; gabarits remplis vérifiés valides.
- Non fait : configurer le plugin Modèles d'Obsidian vers `5. Memoire IA/_gabarits` (réglage du coffre entier, à faire par le user).
- Fait : procédure de branchement d'un harness (`docs/BRANCHER-UN-HARNESS.md`), décisions 16 et 17, `VISION.md` section 7.
- Fait : étape 1 bis. Les 7 types sont dans `_schema.json` (coffre, commit eb03f0a) ; le validateur n'a plus aucun type en dur ; 29 tests verts (16 d'origine inchangés + schéma absent/invalide/mal décrit, type fictif, cohérence `_FORMATS.md`, vrai coffre).
- Fait : `docs/ARCHITECTURE.md` (composants, fonctionnement, conformité au guide, 4 points ouverts) ; `evals/` (format + brouillon de 14 questions, à valider par le user).
- Bloquants : aucun. Tout ce qui suit attend le user :
  1. Étape 2 : remplir à la main 1 ou 2 fiches (l'étape 3 en dépend, elle valide les gabarits).
  2. Relire et compléter `evals/questions.md` (passer les questions en `validee`).
  3. Réfléchir à ce que le résumeur doit retenir d'une session (préalable à l'étape 4).
  4. Accord pour une règle de permission globale qui bloque `D:\Europa` hors `5. Memoire IA` (point ouvert 2 d'`ARCHITECTURE.md`), idéalement avant l'étape 3.
  5. Plugin Modèles d'Obsidian vers `5. Memoire IA/_gabarits`.
- Prochaine action : étape 2, le user remplit à la main 1 ou 2 fiches (ex. `ai-harness`, un cours de maths avec quelques notions) et leur ligne d'`_INDEX.md`, puis lance le validateur.

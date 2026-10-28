# Conventions de travail

Référence lue à la demande (pas chargée à chaque session, contrairement à `CLAUDE.md`). Le détail théorique est dans `GUIDE-ARCHITECTURE-AGENTIQUE.md`, sections 6 (tokens), 7 (anti-patterns) et 9 (méthode).

## Utiliser Claude Code efficacement

- **Une session = une tâche.** Nouvelle tâche sans lien : nouvelle session ou `/clear`. Une session longue paie tout son historique à chaque message.
- **`CLAUDE.md` reste court.** Il est chargé à chaque message ; le détail va ici, dans `VISION.md` ou dans les docs, lus seulement quand la tâche en a besoin.
- **Lire ciblé.** Chercher (Grep, Glob) avant de lire ; lire une section, pas un fichier entier quand c'est inutile ; ne pas relire un fichier qu'on vient d'écrire.
- **Sous-agents pour les recherches larges.** Ils lisent beaucoup et ne renvoient que la conclusion : le contexte principal reste petit.
- **Choisir le modèle à la tâche.**
  - Opus : architecture, prompts d'agents, logique subtile, débogage qui a échoué deux fois.
  - Sonnet : code bien spécifié avec tests, skills, scripts.
  - Haiku : relectures de cohérence, lancer les tests, mises à jour de `PROGRESS.md`.
  - Commencer au niveau le moins cher quand la spécification est précise ; monter après deux échecs.
- **Plan avant code** pour toute tâche non triviale : un plan relu coûte moins cher qu'un code jeté.
- **Les fichiers sont la mémoire de travail.** Une décision qui n'est que dans la conversation est perdue au prochain `/clear` : elle va dans `docs/DECISIONS.md` ou `PROGRESS.md`.

## Code

- Langage par défaut : Python (bibliothèque standard d'abord), venv dans le dossier du projet sur D:.
- Une fonction = une responsabilité ; des noms qui disent ce que ça fait ; pas d'abstraction avant le deuxième usage réel.
- Configuration (chemins, modèles, seuils) dans un seul fichier de config, pas en dur.
- Entrées validées aux frontières (fichiers lus, sorties de modèle) ; échouer clairement plutôt que continuer avec des données douteuses.
- Déterministe là où on décide : passer la date en paramètre plutôt qu'appeler « maintenant » au milieu du code.
- Tests (`pytest`) pour toute logique : parsing des fiches, validation des tags, choix de fichiers à lire.

## Agents et mémoire

- **Un agent = une responsabilité**, avec une entrée et une sortie définies (un format de fichier, un frontmatter).
- **Sortie vérifiable par du code.** Un agent qui écrit une fiche produit un frontmatter que le code valide (tags dans `_TAGS.md`, champs obligatoires, lien source présent).
- **Divulgation progressive.** Un agent lit `_INDEX.md`, puis la fiche projet, puis la fiche composant, et n'ouvre le code qu'à la fin.
- **Traçabilité.** Chaque appel de modèle laisse une trace (modèle, tâche, fichiers lus, tokens si connus) pour comprendre et mesurer.
- **Évaluation.** `evals/` contient des questions réelles posées à la mémoire, avec la réponse ou la fiche attendue. On les rejoue après chaque changement de structure, de gabarit ou de prompt.
- **Une mémoire fausse est pire qu'une mémoire vide.** Dans le doute, l'agent écrit dans l'inbox avec un marqueur « à valider » plutôt que dans une fiche.

## Décisions

Une ligne par décision dans `docs/DECISIONS.md` : date, décision, pourquoi, alternatives écartées, ce qui ferait changer d'avis. Une décision remplacée est marquée, jamais effacée.

## Monter en compétence

- Le user rédige lui-même la première fiche (étape 2) avant que l'agent le fasse, puis compare.
- Pour chaque choix, les sessions expliquent le pourquoi et l'alternative écartée.
- Lire les traces : ce que l'agent a réellement lu, et pourquoi.
- Mesurer avant d'optimiser : tokens consommés, bonne fiche trouvée ou non.

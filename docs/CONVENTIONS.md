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

## Principes d'architecture agentique et leurs sources

Les 14 principes de `GUIDE-ARCHITECTURE-AGENTIQUE.md` (section 2) restent la base. Ce tableau rattache chacun à une référence reconnue (liste complète en section 12 du guide) et ajoute ceux qui manquaient.

| Principe | Source reconnue | Application ici |
|---|---|---|
| Commencer simple ; workflow avant agent autonome ; ajouter de la complexité seulement si une mesure le justifie | Anthropic, *Building Effective Agents* ; OpenAI, *A Practical Guide to Building Agents* (un seul agent d'abord) | Coffre + grep avant base vectorielle ; fiches à la main avant consolidation automatique |
| Le contexte est une ressource finie : le plus petit ensemble d'informations à fort signal, récupéré au moment où on en a besoin | Anthropic, *Effective Context Engineering for AI Agents* | Pyramide de zoom ; `CLAUDE.md` court, le reste lu à la demande |
| Prise de notes structurée hors du contexte, compaction, sous-agents qui renvoient un résumé | Anthropic, *Effective Context Engineering* ; *How We Built Our Multi-Agent Research System* | `PROGRESS.md`, `DECISIONS.md`, fiches du coffre |
| Être maître de ses prompts et de sa fenêtre de contexte ; petits agents focalisés ; état explicite, reprise possible | HumanLayer, *12-Factor Agents* (facteurs 2, 3, 5, 10, 12) | Prompts versionnés dans le dépôt ; un agent = une tâche ; état dans des fichiers, pas dans la session |
| Le multi-agents coûte cher et perd de l'information ; partager le contexte et les décisions, pas seulement la consigne | Cognition, *Don't Build Multi-Agents* ; Anthropic (multi-agents ≈ beaucoup plus de tokens qu'une session simple) | Un seul consolidateur ; sous-agents réservés à la lecture large |
| Les outils sont une interface pour le modèle : peu d'outils, noms et descriptions précis, erreurs qui disent quoi faire | Anthropic, *Writing Effective Tools for Agents* (et l'« ACI » de *Building Effective Agents*) | La skill `memoire` et ses scripts ont des sorties courtes et explicites |
| Planification, mémoire et outils sont les trois composants d'un agent | Lilian Weng, *LLM Powered Autonomous Agents* | Le harness couvre la mémoire en premier |
| Mémoire hiérarchique : un noyau toujours en contexte, une archive consultée à la demande | Article MemGPT (Letta) | `_INDEX.md` = noyau ; fiches = archive |
| Récupérer selon pertinence, récence et importance ; consolider par « réflexion » périodique | Park et al., *Generative Agents* (2023) | Statut actif/archivé, point quotidien, fiches bilan |
| Le contenu externe est une donnée, jamais une instruction ; ne pas réunir données privées + contenu non fiable + moyen de sortie | Simon Willison, injection de prompt et *lethal trifecta* ; OWASP Top 10 LLM (LLM01 injection, LLM06 agentivité excessive) | Contenu scrapé marqué `source: externe` ; un agent qui lit du web n'écrit que dans l'inbox et n'a ni réseau sortant ni accès au reste du coffre |
| Vérifier, évaluer en continu sur un jeu de cas fixe | Anthropic, *Building Effective Agents* (évaluateur-optimiseur) et sa doc sur les évals | `evals/` rejoué après chaque changement |
| Explorer, planifier, coder, committer ; `CLAUDE.md` court et précis ; `/clear` entre les tâches | Anthropic, bonnes pratiques Claude Code | Boucle de travail de `CLAUDE.md` |

## Décisions

Une ligne par décision dans `docs/DECISIONS.md` : date, décision, pourquoi, alternatives écartées, ce qui ferait changer d'avis. Une décision remplacée est marquée, jamais effacée.

## Monter en compétence

- Le user rédige lui-même la première fiche (étape 2) avant que l'agent le fasse, puis compare.
- Pour chaque choix, les sessions expliquent le pourquoi et l'alternative écartée.
- Lire les traces : ce que l'agent a réellement lu, et pourquoi.
- Mesurer avant d'optimiser : tokens consommés, bonne fiche trouvée ou non.

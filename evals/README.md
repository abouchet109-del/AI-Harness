# Évaluations de la mémoire

On ne sait si la mémoire marche qu'en lui posant de vraies questions. Ce dossier contient ces questions, avec ce qu'on attend comme réponse et comme chemin de lecture. On les rejoue après chaque changement de structure, de gabarit, de prompt ou de modèle (voir `docs/CONVENTIONS.md`).

## Format d'une question (`questions.md`)

Chaque question a :

- **id** : `Q01`, `Q02`… (jamais réutilisé, même si la question est supprimée) ;
- **catégorie** : `projet`, `transverse`, `etudes`, `cycle-de-vie`, `absent`, `securite` ;
- **question** : formulée comme le user ou un agent la poserait ;
- **fiches attendues** : les fiches que le zoom doit atteindre ;
- **réponse attendue** : les éléments qui doivent y être (pas une phrase exacte) ;
- **budget** : le nombre maximal de fichiers lus pour y répondre (le zoom doit rester économe) ;
- **statut** : `brouillon` (proposé, pas validé par le user), `validee`, ou `en-attente` (les fiches n'existent pas encore).

Les catégories couvrent les cinq capacités que mesure LongMemEval (Wu et al., ICLR 2025) :

| Capacité | Catégories ici |
|---|---|
| Extraire une information | `projet`, `etudes` |
| Raisonner sur plusieurs sessions ou projets | `transverse` |
| Raisonner dans le temps (dates, échéances, ordre des événements) | `etudes`, `cycle-de-vie` |
| Intégrer une mise à jour (l'information a changé) | `cycle-de-vie` ; des questions de mise à jour s'ajouteront avec le consolidateur (étape 5) |
| S'abstenir quand l'information n'existe pas | `absent` |

`securite` s'y ajoute, propre à ce projet (injection, frontière du coffre perso).

## Ce qu'on mesure à chaque passage

| Mesure | Comment |
|---|---|
| Bonne fiche atteinte | Les fiches attendues font partie des fichiers lus |
| Réponse correcte | Tous les éléments attendus sont présents, rien d'inventé |
| Économie | Nombre de fichiers lus ≤ budget ; tokens consommés si connus |
| Honnêteté | Pour `absent` : la réponse dit « pas dans la mémoire » au lieu d'inventer |

Les résultats de chaque passage vont dans `evals/resultats/AAAA-MM-JJ-<sujet>.md`. Le script qui rejoue les questions viendra avec l'étape 3 (skill `memoire`).

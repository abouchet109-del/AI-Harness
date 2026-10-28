# Brancher un harness sur la mémoire

Procédure à suivre chaque fois qu'un nouveau harness (prof de maths, Anki, veille hackathon…) doit lire ou alimenter la mémoire, et surtout quand il apporte un type d'information que la structure actuelle ne sait pas stocker. C'est de l'**évolution de schéma** : le même problème que les migrations de base de données ou les registres de schémas des systèmes à messages, avec les mêmes règles.

## Principes

- **La structure décrit des types d'information, pas des outils.** Anki n'a pas de type « Anki » : il apporte des niveaux de maîtrise et des révisions, qui vont dans `notion`. Sinon la mémoire générale devient une juxtaposition de silos, un par outil.
- **La structure est le contrat de tout le système.** Le validateur, le consolidateur, la skill `memoire` et chaque harness déjà branché en dépendent. Elle ne change que par cette procédure, avec l'accord du user. Aucun agent ne la modifie de lui-même, et un harness jamais.
- **Ajouter plutôt que modifier.** Un ajout (type, champ facultatif, tag) ne casse rien. Une modification (renommer, supprimer, changer le sens d'un champ) casse les fiches et les harness existants : elle demande une migration.
- **Le schéma est une donnée.** Les types, champs et règles sont décrits dans `_schema.json` du coffre, lu par le validateur. Ajouter un type ne demande pas de modifier du code Python.

## Étapes

### 1. Le manifeste du harness

Écrire `docs/harnesses/<nom>.md` dans ce dépôt (à la main ou avec une session) :

- **Nom, dépôt, rôle** en une phrase.
- **Ce qu'il lit** dans la mémoire : quels dossiers, quels types de fiche.
- **Ce qu'il écrit** : les informations qu'il produit, avec 2 ou 3 exemples réels de notes d'inbox.
- **Provenance** : `interne` (produit par le user ou ses outils) ou `externe` (web, documents reçus).
- **Données brutes** : où il les garde (elles ne vont pas dans le coffre), et à quel volume.
- **Fréquence** d'écriture.

Le code du harness reste un projet : il a sa fiche dans `Projets/`, comme les autres.

### 2. La correspondance avec l'existant

Une session (Opus, effort high : c'est du jugement) lit le manifeste, `_FORMATS.md`, `_schema.json` et `_TAGS.md`. Pour chaque information du harness, elle cherche dans cet ordre, et s'arrête au premier qui convient :

1. **Un type et des champs existants** suffisent : rien à changer.
2. **Un champ facultatif** à ajouter à un type existant (exemple : `retention_anki` sur `notion`).
3. **Un tag** à ajouter dans une facette existante (exemple : `type/examen`).
4. **Une facette** nouvelle.
5. **Un nouveau type de fiche**, en dernier recours, avec la raison pour laquelle aucun type existant ne convient.

Elle rend une proposition : un tableau information → décision → justification, la liste des fichiers modifiés (diff), les fiches et harness existants touchés, et si le changement est un ajout ou une modification.

**Garde-fou :** la proposition part du manifeste écrit par le user, jamais du contenu traité par le harness. Une page web scrapée ne doit pas pouvoir faire évoluer la structure, même indirectement.

### 3. La validation

Le user lit la proposition et accepte, corrige ou refuse. Rien n'est appliqué avant.

### 4. L'application (Sonnet, effort medium)

Tout dans le même commit du coffre, et le même commit du dépôt AI-Harness :

- [ ] `_schema.json` : le type ou le champ, et la version du schéma incrémentée.
- [ ] `_gabarits/<type>.md` pour un nouveau type.
- [ ] `_TAGS.md` pour les tags et facettes.
- [ ] `_FORMATS.md` : la description lisible, cohérente avec le schéma (un test le vérifie).
- [ ] `_INDEX.md` : une section si le type ouvre un nouveau point d'entrée du zoom.
- [ ] Tests du validateur : au moins un cas valide et un cas invalide par type ou champ ajouté.
- [ ] Le prompt du consolidateur et la skill `memoire`, une fois qu'ils existent, s'ils doivent connaître le nouveau type.
- [ ] `evals/` : au moins une question qui fait appel à la nouvelle information.
- [ ] `docs/DECISIONS.md` : une ligne (ce qui a été ajouté et pourquoi, l'alternative écartée).
- [ ] Le manifeste, mis à jour avec la décision finale.

### 5. La vérification (Haiku, effort low)

Validateur sur tout le coffre, tests, évals. Puis une première vraie note d'inbox du harness, consolidée et validée.

## Une modification (changement incompatible)

Renommer, supprimer ou changer le sens d'un champ ou d'un type :

1. Un script `scripts/migrations/NNN-<sujet>.py`, idempotent, qui transforme les fiches existantes (avec un mode simulation qui affiche ce qu'il changerait).
2. Lancement en simulation, relecture par le user, puis pour de vrai, dans un commit du coffre à part (annulable par `git revert`).
3. Les harness qui utilisaient l'ancien format sont mis à jour dans la foulée.
4. Validateur, tests et évals avant de considérer la migration finie.

Un type qui a encore des fiches n'est jamais supprimé sans migration.

## Exemples attendus

- **Prof de maths** : lit `Etudes/`, écrit des séances et des exercices faits → types `cours`, `notion`, `travail` existants. Rien à changer.
- **Anki** : écrit des synthèses de révision → `notion`, avec peut-être un champ facultatif `retention_anki`.
- **Veille hackathon** : écrit des hackathons repérés, provenance externe → probablement un nouveau type `hackathon` dans `Veille/Hackathons/` (dates, lieu, thème, statut de candidature). C'est le seul cas prévu de nouveau type à ce jour.

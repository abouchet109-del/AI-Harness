# Vision : la mémoire centrale

Document de conception de la brique centrale de l'AI-Harness. Il complète `GUIDE-ARCHITECTURE-AGENTIQUE.md` (section 4.5 Mémoire) avec les choix propres à ce projet.

## Ce que je veux

- Une mémoire de tous mes projets (code, architectures, agents, idées, historique) qui dépasse la fenêtre de contexte.
- Une brique centrale à laquelle d'autres briques se branchent et écrivent : veille hackathon, prof de maths, etc.
- Alimentation **automatique**, avec **un point quotidien** sur ce qui a été ajouté, modifié ou archivé.
- Support : **coffre Markdown Obsidian** (déjà utilisé).
- **Outils gratuits** uniquement.
- La mémoire suit le **cycle de vie** des projets : un projet en cours est connu comme tel ; une fois fini, le brut est archivé et la mémoire garde une synthèse (ce que c'était, ce qui a été codé, les idées, l'archi).
- Un agent qui cherche quelque chose dans un autre projet **zoome** sur ce dont il a besoin au lieu de tout rescanner.

## Choix de conception

### 1. Pyramide de résumés + tags à facettes (et pas un arbre unique)

Un seul arbre de classement (code → langage → type → projet → fonction) casse vite : un même élément appartient à plusieurs branches (un agent Python qui fait du scraping pour un hackathon est à la fois « Python », « agent », « scraping » et « hackathon X »). On sépare donc deux choses :

- **La pyramide de zoom = des niveaux de résumé**, du plus court au plus détaillé :
  1. `_INDEX.md` : une ligne par projet (statut, une phrase, tags).
  2. Fiche projet : objectif, idées, archi, liste des composants (≈ 1 écran).
  3. Fiche composant : ce que fait la brique, interface, choix techniques, chemin vers le code.
  4. Le code source lui-même, dans le dépôt du projet (jamais copié dans le coffre).

  Un agent lit le niveau 1, choisit, descend au niveau 2, puis 3, et n'ouvre le code qu'à la fin. Chaque niveau coûte peu de tokens.

- **Le classement = des tags hiérarchiques à facettes** (Obsidian supporte `#a/b/c`), dans le frontmatter :
  - `domaine/` : `code`, `maths`, `veille`…
  - `langage/` : `python`, `typescript`…
  - `type/` : `agent`, `brique-archi`, `site-web`, `algo`, `scraper`…
  - `projet/` : `open-agent-hack`, `prof-maths`…
  - `statut/` : `actif`, `archive`, `idee`

  On combine les facettes pour filtrer (« tous les `type/agent` en `langage/python` »), au lieu de suivre un seul chemin.

- **Vocabulaire contrôlé** : la liste des tags autorisés vit dans `_TAGS.md`. Les agents n'inventent pas de tags (sinon `#python`, `#Python`, `#py` coexistent et le filtrage ne marche plus). Un nouveau tag passe par le point quotidien.

- **Filet de sécurité** : recherche plein texte (grep) sur le coffre quand les tags ne suffisent pas. Recherche sémantique (embeddings locaux) seulement plus tard, si le grep s'avère insuffisant.

### 2. Deux types de mémoire, séparés

- **Mémoire « méta »** (sur mes projets) : fiches projet et composant, décisions, idées. Dans le coffre.
- **Mémoire « données »** (ce que les briques traitent) : cours, notions, exercices, travaux, hackathons scrapés. Le **contenu à apprendre/réutiliser** va dans le coffre (une note par cours, par notion, par hackathon notable). Les **données brutes en volume** (tous les résultats de scraping) restent dans le stockage de la brique (SQLite/JSON dans son dossier) ; le coffre n'en garde qu'une synthèse et un lien. Sinon le coffre gonfle et la recherche se dégrade.

  Exemple, les études : `Etudes/<cours>/` contient la fiche cours (échéances, reste à faire), une fiche par notion (maîtrise 0-4, dernière révision, suivi daté) et une par travail (deadline, documents). Anki reste la source de vérité de ses cartes et de leur planning ; son adaptateur dépose une synthèse dans l'inbox. Le code d'un harness (Anki, prof de maths) est, lui, un projet dans `Projets/`.

- **Se brancher à la mémoire** : un harness lit en suivant la pyramide et écrit uniquement dans l'inbox, au format de `_FORMATS.md` (le contrat, vérifié par `scripts/valider_fiches.py`). Il n'a pas besoin de connaître le reste.

### 3. Écriture via une boîte de réception

Les briques et les sessions n'écrivent pas directement partout dans le coffre :

1. Elles déposent une note brute dans `00-Inbox/` (format commun : titre, source, date, tags proposés, texte).
2. Un agent de consolidation classe : met à jour la fiche concernée, crée une fiche si besoin, fusionne les doublons, applique le vocabulaire de tags.

Un seul agent touche à la structure, ce qui évite les doublons et les fiches contradictoires.

Sources d'alimentation :
- Sessions Claude Code : hook de fin de session qui écrit un résumé dans l'inbox.
- Briques (veille hackathon, prof de maths) : un petit adaptateur par brique qui écrit au format commun.

### 4. Cycle de vie d'un projet

- `statut/actif` : la fiche projet porte un bloc « état actuel » (où on en est, prochaine étape), mis à jour par la consolidation.
- Passage en `statut/archive` (manuel ou détecté) :
  1. Le brut (code, README, agents, historique) reste dans le dépôt git du projet, ou part dans `D:\Archives\<projet>`. La fiche garde le lien.
  2. Un agent rédige une **fiche post-mortem** : ce qu'était le projet, ce qui a été codé, l'archi, les idées (retenues et abandonnées), ce qui est réutilisable.
  3. Le bloc « état actuel » est retiré ; les composants réutilisables gardent leur fiche.

### 5. Le point quotidien

- Le coffre est un **dépôt git** : chaque passage de consolidation fait un commit. Le diff des dernières 24 h donne gratuitement « ce qui a changé ».
- Une tâche planifiée quotidienne lit ce diff et écrit `Journal/AAAA-MM-JJ.md` : nouveautés, modifications, archivages, tags proposés, points douteux à valider.
- Je relis dans Obsidian et je corrige si besoin ; `git revert` en cas de mauvaise consolidation.

### 6. Accès depuis les agents

- Une **skill `memoire`** décrit la procédure de zoom (lire `_INDEX.md` → fiche projet → fiche composant → code) et les règles d'écriture (inbox uniquement).
- Le coffre est ajouté comme dossier accessible aux sessions Claude Code. Pas de serveur MCP au début : lire des fichiers Markdown suffit. Un serveur MCP (recherche, sémantique) se rajoute plus tard sans changer la structure.

## Structure du coffre (créée le 2026-10-28)

```
D:\Europa\5. Memoire IA/
  _INDEX.md            niveau 1 : tous les projets et cours, une ligne chacun
  _TAGS.md             vocabulaire de tags autorisé
  _FORMATS.md          le contrat : types de fiche, champs, règles
  _gabarits/           un gabarit par type de fiche
  00-Inbox/            dépôts bruts des sessions et des briques
  Projets/<projet>/
    <projet>.md        niveau 2 : fiche projet (idée, actif, ou bilan si archivé)
    composants/*.md    niveau 3 : fiches composant
  Connaissances/       ce qui sert dans plusieurs projets (patterns, leçons)
  Etudes/<cours>/
    <cours>.md         fiche cours
    notions/*.md       fiches notion
    travaux/*.md       fiches travail (exposé, devoir, examen)
  Veille/Hackathons/   hackathons notables (brique veille, format à définir)
  Journal/             points quotidiens (format à définir, étape 6)
```

## Ordre de construction

1. Structure du coffre, `_INDEX.md`, `_TAGS.md`, gabarits de fiches, git init.
2. Remplir à la main 1 ou 2 projets existants (ex. open-agent-hack) pour valider les gabarits.
3. Skill `memoire` (lecture/zoom) et test depuis une session sur un autre projet.
4. Hook de fin de session → inbox.
5. Agent de consolidation (inbox → fiches).
6. Point quotidien planifié.
7. Cycle de vie : archivage et fiche post-mortem.
8. Adaptateurs des briques (veille hackathon, prof de maths, Anki). Le prof de maths peut se construire en parallèle dès l'étape 1 : il ne dépend que de `_FORMATS.md`.
9. Plus tard, si besoin : recherche sémantique locale, serveur MCP.

## Modèle et effort par étape

Deux choix distincts : le modèle de la session qui **construit** l'étape, et celui de l'agent qui **tourne** ensuite (coût récurrent). Valeurs de départ, à ajuster selon les mesures ; monter d'un cran après deux échecs.

| Étape | Construction | Exécution récurrente | Pourquoi |
|---|---|---|---|
| 1. Structure, index, tags, gabarits | Opus, medium | — | Les gabarits fixent tout le reste ; peu de fichiers, beaucoup de discussion |
| 2. Premières fiches | Le user à la main ; comparaison avec Sonnet, medium | — | Apprendre ce qui compte avant d'automatiser |
| 3. Skill `memoire` (zoom) | Sonnet, high | Le modèle de la session qui l'appelle | Procédure claire, mais elle doit marcher depuis n'importe quel projet |
| 4. Hook de fin de session → inbox | Prompt de résumé : Opus, high. Code du hook : Sonnet, medium | Haiku (à confirmer par les évals, sinon Sonnet) | Le prompt décide ce qui est retenu ; le résumé tourne à chaque session, donc il doit être bon marché |
| 5. Agent de consolidation | Opus, high | Sonnet | Cœur du système ; une erreur crée un faux souvenir |
| 6. Point quotidien | Sonnet, medium | Haiku | Lecture d'un diff git et rédaction d'une note |
| 7. Archivage et fiche bilan | Prompt de bilan : Opus, medium. Code : Sonnet, medium | Sonnet | Rare, mais la fiche bilan doit être fidèle |
| 8. Adaptateurs des briques | Sonnet, medium | Haiku | Transformation de format, bien spécifiée |
| 9. Recherche sémantique (si besoin) | Décision et évals : Opus, high. Code : Sonnet, medium | Embeddings locaux, sans LLM | Ne se justifie que si les évals montrent un manque |
| Transverse : relectures, tests, évals, `PROGRESS.md` | Haiku, low | — | Mécanique |

## Questions ouvertes

- ~~Coffre Obsidian existant~~ : tranché (décision 3), la mémoire vit dans `D:\Europa\5. Memoire IA` avec son propre git.
- Rétention des conversations : Claude Code supprime par défaut les transcripts de plus de 30 jours (`cleanupPeriodDays`). À augmenter pour pouvoir ingérer après coup le travail fait avant que la mémoire soit prête.
- Le point quotidien : seulement une note dans Obsidian, ou aussi une notification ?
- L'agent de consolidation tourne-t-il à chaque fin de session, ou une fois par jour avant le point ?

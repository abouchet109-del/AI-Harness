# Fondements de la mémoire

Ce que disent les neurosciences, les sciences des organisations et la littérature sur les agents à mémoire, simplifié et traduit en règles pour ce projet. Le but n'est pas d'imiter le cerveau : c'est de reprendre des mécanismes éprouvés là où ils résolvent un problème réel de notre architecture, et seulement là.

Chaque section donne la source, ce qu'elle établit, la règle qu'on en tire, et où elle s'applique. Les règles retenues sont reportées dans `VISION.md` et `docs/DECISIONS.md`.

## Neurosciences de la mémoire

### Deux systèmes : capture rapide, intégration lente

**Source.** McClelland, McNaughton et O'Reilly (1995), *Why there are complementary learning systems in the hippocampus and neocortex*, Psychological Review ; mise à jour pour l'IA par Kumaran, Hassabis et McClelland (2016), *What learning systems do intelligent agents need?*, Trends in Cognitive Sciences.

**Ce qu'elle établit.** Le cerveau sépare deux fonctions. L'hippocampe enregistre vite chaque épisode, tel quel. Le néocortex intègre lentement ces épisodes dans les connaissances durables, surtout pendant le sommeil, en les « rejouant » mêlés aux connaissances existantes. Intégrer trop vite détruit l'ancien savoir (l'« interférence catastrophique »).

**Règle.** On garde deux temps distincts. L'inbox capture vite et sans transformer. La consolidation intègre **une fois par jour**, en un passage, comme le sommeil, en confrontant chaque note aux fiches existantes plutôt qu'en ajoutant une fiche par événement.

**Où.** Étape 5 (consolidateur) et tâche quotidienne. Tranche la question ouverte « à chaque session ou une fois par jour » : une fois par jour.

### Un schéma existant accélère l'intégration

**Source.** Tse et al. (2007), *Schemas and memory consolidation*, Science.

**Ce qu'elle établit.** Une information qui s'insère dans un schéma mental déjà formé se consolide beaucoup plus vite qu'une information sans cadre.

**Règle.** Le schéma du coffre (`_schema.json`) joue ce rôle. Une note d'inbox qui rentre dans un type existant est consolidée directement. Une note qui ne rentre dans **aucun** type n'est pas forcée dans le plus proche : elle reste dans l'inbox, marquée « hors schéma », et apparaît dans le point quotidien. Si ça se répète, c'est le signal d'un branchement à faire (`docs/BRANCHER-UN-HARNESS.md`).

**Où.** Étape 5.

### Se rappeler rend la mémoire modifiable

**Source.** Nader, Schafe et LeDoux (2000), *Fear memories require protein synthesis in the amygdala for reconsolidation after retrieval*, Nature.

**Ce qu'elle établit.** Un souvenir rappelé redevient instable et est réécrit : chaque rappel est une occasion de le déformer.

**Règle.** C'est exactement le risque d'un consolidateur qui réécrit une fiche entière à chaque passage : de résumé en résumé, la fiche dérive (le « téléphone arabe »). Le consolidateur ne réécrit donc **jamais** une fiche entière. Il propose des opérations limitées, appliquées par du code (voir Mem0 plus bas), et chaque modification apparaît en diff dans le point quotidien.

**Où.** Étape 5, et rédacteur de bilan (étape 7).

### Les faux souvenirs viennent de la perte de la source

**Source.** Johnson, Hashtroudi et Lindsay (1993), *Source monitoring*, Psychological Bulletin.

**Ce qu'elle établit.** On se souvient souvent d'un contenu sans savoir d'où il vient ; c'est la première cause de faux souvenirs (prendre une idée imaginée pour un fait vécu, une rumeur pour une information vérifiée).

**Règle.** Déjà appliquée au niveau de la fiche (`sources` obligatoire, `provenance` dans l'inbox). On la descend au niveau du fait : toute ligne ajoutée par le consolidateur dans le corps d'une fiche porte sa source entre parenthèses (session, commit, note). Un fait sans source n'est pas écrit.

**Où.** Étape 5 et validateur (vérification possible par motif).

### Oublier est utile

**Source.** Anderson et Schooler (1991), *Reflections of the environment in memory*, Psychological Science.

**Ce qu'elle établit.** La facilité de rappel d'un souvenir suit la probabilité qu'on en ait besoin, estimée par sa récence et sa fréquence. L'oubli n'est pas un défaut : il garde accessible ce qui sert.

**Règle.** On n'efface pas, on **rétrograde**. Un projet archivé est réduit à son bilan ; l'index range par statut puis par date de mise à jour ; l'inbox est vidée après consolidation ; le journal pourra être compacté par mois. On ne compte pas les consultations : il faudrait écrire à chaque lecture, ce qui casserait la règle d'un seul écrivain et coûterait des tokens pour un gain incertain.

**Où.** Étapes 5 à 7, générateur d'index.

## Sciences des organisations

### Savoir qui sait quoi

**Source.** Wegner (1987), *Transactive memory: A contemporary analysis of the group mind*.

**Ce qu'elle établit.** Un groupe efficace ne stocke pas tout chez chacun : il partage un annuaire de qui sait quoi, et va chercher l'information chez le bon membre.

**Règle.** La mémoire est cet annuaire. Elle sait que le détail du planning Anki est dans Anki, que le code est dans tel dépôt, que les hackathons bruts sont dans `state/hackwatch.db`. Chaque fiche dit **où vit la vérité détaillée**, et la mémoire ne la recopie pas.

**Où.** Déjà le cas (décision : données brutes hors coffre) ; à vérifier dans chaque manifeste de harness.

### Une connaissance sans son contexte est inutilisable

**Source.** Walsh et Ungson (1991), *Organizational memory*, Academy of Management Review.

**Ce qu'elle établit.** Les organisations conservent des décisions, mais perdent souvent leur raison d'être ; la décision devient alors impossible à réutiliser ou à remettre en cause à bon escient.

**Règle.** Une décision se garde avec son pourquoi, l'alternative écartée et ce qui ferait changer d'avis (déjà le format de `DECISIONS.md`). Le consolidateur garde la même structure quand il reporte une décision dans une fiche.

**Où.** Étape 5, gabarits.

### Le bilan structuré (After Action Review)

**Source.** US Army, *A Leader's Guide to After-Action Reviews* (TC 25-20, 1993) ; méthode reprise depuis dans de nombreuses organisations.

**Ce qu'elle établit.** Un retour d'expérience utile répond à quatre questions : qu'est-ce qui était prévu ? qu'est-ce qui s'est passé ? pourquoi l'écart ? que garder et que changer la prochaine fois ?

**Règle.** La section bilan d'une fiche projet archivée suit ces quatre questions, plus « ce qui est réutilisable » (composants, idées). C'est aussi une bonne grille pour le résumeur de session.

**Où.** Étape 7 (gabarit de bilan), étape 4.

### Les bases de « leçons apprises » échouent quand on attend qu'on vienne les lire

**Source.** Weber, Aha et Becerra-Fernandez (2001), *Intelligent lessons learned systems*, Expert Systems with Applications ; constat récurrent de la gestion des connaissances.

**Ce qu'elle établit.** Les systèmes de leçons apprises passifs (une base qu'on consulte si on y pense) sont peu utilisés. Ceux qui marchent apportent la leçon au moment où elle sert.

**Règle.** La skill `memoire` répond quand on la sollicite, mais ça ne suffira pas : il faudra un mécanisme qui **pousse** quelques lignes pertinentes au bon moment (au début d'une session sur un projet, par exemple). C'est un compromis avec le coût en tokens : à réfléchir (voir la fin du document).

## Littérature sur les agents à mémoire

### Mémoire hiérarchique

**Source.** Packer et al. (2023), *MemGPT: Towards LLMs as Operating Systems*.

**Règle reprise.** Un noyau toujours lu (`_INDEX.md`) et une archive consultée à la demande (les fiches). Déjà en place.

### Récence, importance, pertinence, et réflexion

**Source.** Park et al. (2023), *Generative Agents: Interactive Simulacra of Human Behavior*.

**Ce qu'elle établit.** Les agents récupèrent leurs souvenirs selon trois critères combinés (récence, importance, pertinence) et produisent périodiquement des « réflexions », synthèses de plus haut niveau tirées des souvenirs bruts.

**Règle reprise.** Le point quotidien et les fiches `connaissance` sont nos réflexions. Pour la récupération, les tags et le statut font office de pertinence et d'importance, `maj` de récence. Pas de score calculé tant que les évals n'en montrent pas le besoin.

### Mettre à jour par opérations, pas par réécriture

**Source.** Chhikara et al. (2025), *Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory*, arXiv 2504.19413, et la documentation de Mem0.

**Ce qu'elle établit.** Pour chaque nouveau fait, Mem0 récupère les souvenirs proches et fait choisir au modèle une opération parmi quatre : ajouter, mettre à jour, supprimer (le fait contredit), ne rien faire.

**Règle reprise, adaptée.** Le consolidateur ne rend pas des fiches réécrites mais une liste d'opérations, en JSON, que le code applique puis que le validateur vérifie :

| Opération | Effet |
|---|---|
| `ajouter` | Une ligne dans une section d'une fiche existante, avec sa source |
| `creer` | Une nouvelle fiche, depuis le gabarit de son type |
| `remplacer` | Une ligne devenue fausse est marquée remplacée (barrée, avec date et source de la nouvelle) ; l'ancienne reste visible |
| `champ` | Changer une valeur du frontmatter (statut, maîtrise, échéance) |
| `rien` | La note n'apporte rien de nouveau |
| `hors_schema` | La note ne rentre dans aucun type : elle reste dans l'inbox |

Pas de suppression : on garde la trace de ce qui a changé (Walsh et Ungson), et git garde le reste. C'est l'application directe de « le modèle propose, le code décide », et la parade à la reconsolidation.

**Où.** Étape 5.

### Ce qu'il faut évaluer

**Source.** Wu et al. (2025), *LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory*, ICLR 2025.

**Ce qu'elle établit.** Cinq capacités distinctes : extraire une information, raisonner sur plusieurs sessions, raisonner dans le temps, intégrer une mise à jour, et s'abstenir quand l'information n'existe pas. Les assistants testés perdent environ 30 % de précision sur les interactions longues.

**Règle reprise.** Les catégories de `evals/` couvrent ces cinq capacités (correspondance dans `evals/README.md`).

## Ce qui reste à ta réflexion

1. **Que retient le résumeur de session (étape 4) ?** Proposition de départ, tirée de l'After Action Review et du contrôle de la source :
   - les décisions prises, avec le pourquoi et l'alternative écartée ;
   - les erreurs rencontrées, leur cause et leur correction ;
   - les idées, retenues ou abandonnées, et pourquoi ;
   - l'état du projet et la prochaine action ;
   - les composants créés ou modifiés, avec leur chemin ;
   - chaque point avec sa source (identifiant de session, commit).

   Ce qu'on ne garde pas : les essais intermédiaires sans leçon, le détail des commandes, le contenu des fichiers (git l'a déjà). Une session qui n'a modifié aucun fichier et compte peu d'échanges ne produit pas de note. À toi d'ajuster cette liste avant l'étape 4.
2. **Pousser la mémoire au bon moment** (leçons apprises) : au début d'une session sur un projet, injecter 3 à 5 lignes (fiche du projet, dernières décisions, échéances proches) ? C'est utile mais ça coûte des tokens à chaque session. À décider après l'étape 3, mesures à l'appui.
3. **Sauvegarde du coffre hors du PC** : aujourd'hui le git du coffre est seulement local, par choix de confidentialité. Un dépôt GitHub privé servirait de sauvegarde. À toi de peser.

# Fiche d'équipe — Jalon 1

V01 du 16/10/2026 · à relire par les 4 membres

## Informations demandées par le sujet

| Rubrique | Réponse |
|---|---|
| Nom de l'équipe | **À choisir** : « NomEquipe » sert de nom provisoire dans les fichiers (tâche T13) |
| Département confié | Ressources humaines (groupe 6) |
| Membres du groupe | 1. Antoine · 2. Suzanne · 3. Hugo · 4. Alexandre |
| Chef de projet initial | Antoine, comme premier Scrum Master de la rotation (à confirmer) |
| Outil Kanban utilisé | Provisoire : `01_Cadrage/J01_NomEquipe_RH_Kanban_V01.xlsx`. Proposé : GitHub Projects sur le dépôt de l'équipe (tâche T14) |
| Lien vers l'espace partagé | Drive : https://drive.google.com/drive/folders/188Qo1PD5o_uj00p9zyI1fX395_f7BA7h · Dépôt : https://github.com/Syhard87/ProjetFilRouge_BigData |

## Rôles

| Membre | Rôle principal | Responsabilités au jalon 1 | Binôme |
|---|---|---|---|
| Antoine | Data Architect / Data Engineer | Dépôt des sources, audit des données, script rejouable, carte des liens, Kanban, journal des décisions | Data, avec Suzanne |
| Suzanne | BI Developer / Data Analyst | Relecture de l'audit côté indicateurs, matrice indicateurs × sources, pré-analyse graphique des anomalies | Data, avec Antoine |
| Hugo | Business Analyst / Consultant métier | Questions client (métier, processus, KPI), note de compréhension, préparation des entretiens du jalon 2 | Métier, avec Alexandre |
| Alexandre | Responsable Qualité, Tests, Sécurité et IA | Questions sécurité et RGPD, registre des risques, futurs contrôles qualité | Métier, avec Hugo |

**Scrum Master.** La fiche initiale indique que les quatre membres assurent le rôle de Scrum Master. Nous proposons une **rotation** pour que chacun anime à tour de rôle, sans cumul permanent avec un rôle technique lourd. L'ordre et la durée de chaque tour restent à fixer en équipe : par exemple un membre par jalon, en commençant par Antoine.

## Règles de fonctionnement

Règles imposées par le sujet :

- un espace partagé unique et l'arborescence commune des 12 dossiers (`01_Cadrage` à `12_Soutenance`) ;
- un Kanban à 5 colonnes (À faire, En cours, À valider, Terminé, Bloqué) ; chaque tâche a un responsable et une date cible ;
- un journal des décisions, un registre des risques et un journal des anomalies tenus à jour ;
- ne jamais modifier en silence une définition de KPI ou une règle de données ;
- ne jamais utiliser de données personnelles réelles ;
- nommer les fichiers selon le modèle `JXX_NomEquipe_RH_NomLivrable_V01.ext` ; un dépôt tardif porte la mention RETARD.

Règles que nous ajoutons :

- **Corriger à la source, jamais dans le rapport.** Une donnée fausse devient une anomalie du registre ; la règle de correction est décidée, puis notée dans le journal des décisions.
- **Relecture croisée avant chaque dépôt.** Suzanne relit le travail technique d'Antoine et inversement ; Hugo et Alexandre se relisent mutuellement. Personne ne valide seul son propre travail.
- **Point quotidien le matin** (décidé le 05/10/2026) : fait, à faire, blocages. Le Kanban est mis à jour en séance, et chacun déplace lui-même ses tâches.
- **Les fichiers clients ne sont jamais modifiés.** Ils restent dans `data/raw` et `docs` ; tout traitement passe par un script rejouable.
- **Chacun peut tout défendre.** Chaque membre doit pouvoir expliquer le travail des autres devant le jury, en plus du sien.
- **Outils d'IA.** Tout contenu produit avec un assistant d'IA est relu, vérifié sur les sources et approprié par son responsable avant dépôt. Le journal de contribution le mentionne.

## Engagement de l'équipe

Nous reprenons les six engagements du sujet : travail à quatre avec une contribution visible de chacun, autonomie entre les jalons, Kanban et journaux à jour, analyse de chaque mise en situation, signalement rapide des blocages et collaboration avec les autres départements, respect de la confidentialité et de la sécurité des données.

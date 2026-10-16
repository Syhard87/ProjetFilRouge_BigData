# Note d'avancement — Jalon 1

**Jalon :** J01 · **Équipe :** NomEquipe · **Département :** Ressources humaines · **État au :** 16/10/2026

## Objectif du jalon

Prendre connaissance du dossier client, identifier ce qui est compris, ambigu, contradictoire ou manquant, préparer les questions au client et organiser l'équipe de 4.

## Travaux réalisés

| Livrable attendu | Fichier | État |
|---|---|---|
| Analyse initiale des fichiers | `03_Audit_Donnees/J01_NomEquipe_RH_AnalyseInitiale_V01.md` + classeur `J01_NomEquipe_RH_AuditDonnees_V01.xlsx` + script `audit_sources.py` | À valider |
| Liste structurée et priorisée des questions client | `02_Besoins_Metier/J01_NomEquipe_RH_QuestionsClient_V01.md` / `.xlsx` | À valider |
| Kanban initial | `01_Cadrage/J01_NomEquipe_RH_Kanban_V01.md` / `.xlsx` | À valider |
| Fiche d'équipe | `01_Cadrage/J01_NomEquipe_RH_FicheEquipe_V01.md` | À valider ; nom d'équipe manquant |
| Note de compréhension et hypothèses | `01_Cadrage/J01_NomEquipe_RH_NoteComprehension_V01.md` | À valider |
| Journal des décisions | `01_Cadrage/J01_NomEquipe_RH_JournalDecisions_V01.md` | En cours |
| Registre des risques | `01_Cadrage/J01_NomEquipe_RH_RegistreRisques_V01.md` | À valider |
| Preuves individuelles | `01_Cadrage/J01_NomEquipe_RH_JournalContributions_V01.md` | À compléter par chaque membre |

Chiffres clés : 15 sources analysées, 142 anomalies (41 hautes), 42 questions dont 14 bloquantes, 21 tâches au Kanban.

## Décisions prises

Voir le journal des décisions, D04 à D11. La plus importante est D06 : l'audit a été refait de zéro par un script rejouable, et il remplace la V03. Quatre chiffres de la V03 étaient faux ou mal interprétés, notamment 153 absences finissant avant leur début au lieu de 10.

## Difficultés et blocages

- Le nom d'équipe n'est pas choisi : tous les fichiers portent « NomEquipe ».
- Le dépôt GitHub est public alors qu'il contient des données RH.
- Quatre sources annoncées par le cahier des charges n'ont pas été reçues : onboarding, tickets RH, règles RGPD, mail du directeur RH.
- La date de remise du jalon n'est pas encore connue : les dates du Kanban sont provisoires.

## Actions correctives

- Décision sur le nom et l'outil Kanban au prochain point d'équipe (T13, T14).
- Passage du dépôt en privé (T15).
- Envoi des questions P1 au client, dont M07 sur les sources manquantes (T16).

## Priorités avant le prochain jalon

1. Faire relire et valider les livrables par les 4 membres (relecture croisée).
2. Envoyer les 14 questions P1 au client.
3. Faire remplir le journal de contribution par chaque membre.
4. Lancer le jalon 2 : parties prenantes et guide d'entretien.

## Checklist avant dépôt (§11 du sujet)

- [ ] Le nom des fichiers respecte la convention (bloqué : nom d'équipe à choisir)
- [x] Le livrable principal est présent et s'ouvre correctement
- [x] Les hypothèses et les choix sont expliqués
- [x] Les chiffres ont été contrôlés avec les sources (script rejouable, comparaison avec la V03)
- [x] Le dictionnaire, le catalogue KPI ou la documentation ont été mis à jour (profil des colonnes, matrice des indicateurs)
- [ ] Le Kanban reflète l'état réel du travail (à revoir en équipe)
- [x] Les blocages sont visibles et une action est proposée
- [ ] Chaque étudiant a complété sa preuve de contribution
- [ ] Les données personnelles réelles ont été retirées ou anonymisées (données fictives, mais dépôt public : voir R01)
- [ ] La présentation flash a été répétée

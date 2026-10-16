# Projet Fil Rouge — Big Data RH

Projet d'équipe de transformation Data, BI et IA pour GlobalTech Industries (ONE DATA GROUP), département **Ressources humaines** (groupe 6).

Équipe : Antoine (Data Architect / Data Engineer), Suzanne (BI Developer / Data Analyst), Hugo (Business Analyst), Alexandre (Responsable Qualité, Tests, Sécurité et IA).

## Jalon 1 — Comprendre et organiser

| Livrable | Fichier |
|---|---|
| Analyse initiale des fichiers | [03_Audit_Donnees/J01_NomEquipe_RH_AnalyseInitiale_V01.md](03_Audit_Donnees/J01_NomEquipe_RH_AnalyseInitiale_V01.md) |
| Registre d'anomalies et profilage (Excel) | `03_Audit_Donnees/J01_NomEquipe_RH_AuditDonnees_V01.xlsx` |
| Questions au client, priorisées | [02_Besoins_Metier/J01_NomEquipe_RH_QuestionsClient_V01.md](02_Besoins_Metier/J01_NomEquipe_RH_QuestionsClient_V01.md) |
| Kanban initial | [01_Cadrage/J01_NomEquipe_RH_Kanban_V01.md](01_Cadrage/J01_NomEquipe_RH_Kanban_V01.md) |
| Fiche d'équipe | [01_Cadrage/J01_NomEquipe_RH_FicheEquipe_V01.md](01_Cadrage/J01_NomEquipe_RH_FicheEquipe_V01.md) |
| Note de compréhension et hypothèses | [01_Cadrage/J01_NomEquipe_RH_NoteComprehension_V01.md](01_Cadrage/J01_NomEquipe_RH_NoteComprehension_V01.md) |
| Journal des décisions | [01_Cadrage/J01_NomEquipe_RH_JournalDecisions_V01.md](01_Cadrage/J01_NomEquipe_RH_JournalDecisions_V01.md) |
| Registre des risques | [01_Cadrage/J01_NomEquipe_RH_RegistreRisques_V01.md](01_Cadrage/J01_NomEquipe_RH_RegistreRisques_V01.md) |
| Note d'avancement | [01_Cadrage/J01_NomEquipe_RH_NoteAvancement_V01.md](01_Cadrage/J01_NomEquipe_RH_NoteAvancement_V01.md) |
| Journal individuel de contribution | [01_Cadrage/J01_NomEquipe_RH_JournalContributions_V01.md](01_Cadrage/J01_NomEquipe_RH_JournalContributions_V01.md) |

« NomEquipe » est provisoire, en attendant le choix du nom d'équipe.

## Organisation du dépôt

L'arborescence suit celle imposée par le sujet (`01_Cadrage` à `12_Soutenance`), plus trois dossiers :

- `data/raw/` : les 9 fichiers de données du client, **tels que reçus, jamais modifiés** ;
- `docs/` : les 4 mails (`docs/mails/`) et les 2 PDF de règles (`docs/referentiels/`) du client ;
- `outils/` : les scripts qui génèrent les tableaux du jalon.

## Régénérer les livrables

```bash
pip install -r requirements.txt
python 03_Audit_Donnees/audit_sources.py      # classeur d'audit (142 anomalies)
python outils/generer_tableaux_j01.py         # questions client et Kanban (.xlsx et .md)
```

Les scripts lisent les fichiers clients en lecture seule ; relancés sur les mêmes fichiers, ils redonnent les mêmes chiffres.

## Données

Les données sont fictives, fournies pour un projet pédagogique. Elles comportent néanmoins des rémunérations et des données RH individuelles : le dépôt doit rester privé et les livrables ne montrent que des agrégats.

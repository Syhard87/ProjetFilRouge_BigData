# Note de compréhension de la mission — Jalon 1

Équipe NomEquipe · Ressources humaines · V01 du 16/10/2026 · à relire par les 4 membres

> Cette note dit ce que nous avons compris, pas ce que nous allons construire. Chaque point marqué **H** est une hypothèse à faire valider par le client.

## Le contexte

GlobalTech Industries a acquis des sociétés en France, en Espagne, en Allemagne, en Chine, au Chili et en Pologne. Chacune a gardé ses outils et ses définitions. Côté RH, les processus reposent encore sur des courriels et des fichiers isolés. La direction ne dispose donc pas d'une vision fiable des collaborateurs à l'échelle du groupe.

Notre équipe joue le rôle du cabinet OneData Consulting pour le **département Ressources humaines**. Sa mission : structurer les processus RH et le suivi des collaborateurs. Les KPI indicatifs sont l'effectif, le turnover, l'absentéisme, le recrutement, l'onboarding et les tickets RH. Le prototype attendu comprend un workflow d'arrivée, un tableau de bord RH et un assistant interne encadré.

## Ce que le client demande, à travers ses 4 mails

Les quatre mails sont datés du 13/01/2025. Chacun est un problème de **définition** avant d'être un problème de données :

| Demandeur | Demande | Ce que nous en comprenons |
|---|---|---|
| T. Leroy (COMEX) | « Quel effectif devons-nous présenter ? » Quatre valeurs circulent. | Il veut **une définition gouvernée** de l'effectif, pas un chiffre de plus. Aujourd'hui, l'effectif va de 655 à 800 selon la lecture. |
| C. Dubois (Sales) | Turnover à 35 %, 22 % ou 18 % ? | Il faut **une règle unique** : mobilités internes, fins de CDD, période d'essai. Les fichiers ne contiennent ni motif de sortie ni historique. |
| M. Ruiz (HR Ops) | Écart de masse salariale RH / Finance | Il demande un **rapprochement qui montre les écarts** sans les supprimer. Nous avons déjà identifié deux causes probables : 10 salariés payés hors référentiel et 22 identifiants EXT. |
| E. Schneider (Learning) | Certifications expirées : qui est réellement non conforme ? | Il faut **une règle par site et par poste**, documentée, et une date de référence. Les données n'ont pas de poste. |

## Notre compréhension provisoire

1. **Le premier livrable de valeur est un référentiel salariés fiable.** Effectif, turnover, absentéisme et masse salariale en dépendent tous. Aujourd'hui, il contient des doublons, a perdu 10 personnes et contredit l'organigramme.
2. **La gouvernance compte autant que la technique.** La politique RH dit qu'aucune autorité n'arbitre entre définitions groupe et locales. Sans valideur désigné, nous ne pourrons pas défendre un indicateur.
3. **La confidentialité est une exigence de premier rang.** Les données sont fictives, mais elles comportent des rémunérations individuelles et une enquête dont 255 groupes sur 294 comptent moins de 5 répondants. Les tableaux de bord devront agréger et masquer.
4. **Le dossier est volontairement imparfait.** 142 anomalies sont recensées, et plusieurs sources annoncées manquent : onboarding, tickets RH, règles d'accès RGPD. Notre rôle est de les rendre visibles et de faire trancher, pas de les corriger en silence.

## Hypothèses à valider

| # | Hypothèse | Domaine | Question liée |
|---|---|---|---|
| H1 | La date d'arrêté de l'analyse est le 31/12/2025. | Données | M01 |
| H2 | Le référentiel salariés (S01) fait foi face à l'organigramme (S07). | Données | D05 |
| H3 | Les 10 matricules EMP-00761 à EMP-00770 sont de vrais salariés, effacés par erreur. | Données | D01 |
| H4 | Les 22 EXT-xxxx sont des matricules écrasés (EXT-n ↔ EMP-(n+1)), pas des externes. | Données | D02 |
| H5 | L'effectif COMEX = personnes physiques sous contrat actif à la date d'arrêté, absences longues incluses. | KPI | M03 |
| H6 | Le turnover = départs externes / effectif moyen, hors mobilités internes. | KPI | M04 |
| H7 | Le télétravail n'est pas une absence et sort du calcul d'absentéisme. | KPI | P03, K02 |
| H8 | Les fichiers sont des extraits ; aucun total annuel ne sera extrapolé. | Données | D03 |
| H9 | Les petits groupes (moins de 5 personnes) sont masqués dans toute restitution. | Sécurité | S02 |
| H10 | Le prototype portera d'abord sur l'effectif, l'absentéisme, la conformité des formations et le recrutement ; onboarding et tickets RH attendent leurs sources. | Périmètre | M07, K01 |
| H11 | Architecture cible envisagée : couches brute / nettoyée / analytique (de type médaillon, par exemple sur Microsoft Fabric), avec Power BI branché sur la couche analytique. **À comparer avec au moins un autre scénario aux semaines 7 et 8.** | Architecture | C01 |

Le principe de H11 est déjà appliqué : les fichiers du client sont conservés tels quels avec leur empreinte, et tout traitement passe par un script rejouable. L'arrivée de nouvelles sources, comme la société brésilienne annoncée en semaine 3, n'obligera donc pas à refaire l'existant.

## Hors périmètre à ce stade

- Corriger les données : les règles doivent d'abord être validées.
- Choisir les outils définitifs : c'est le travail des semaines 7 et 8.
- Prendre une décision individuelle automatisée sur un salarié : le guide de rémunération l'interdit.

## Prochaines étapes

1. Relire en équipe l'analyse des fichiers et la liste de questions, puis envoyer les 14 questions P1 au client.
2. Choisir le nom d'équipe et l'outil Kanban ; passer le dépôt GitHub en privé.
3. Préparer le jalon 2 : cartographie des parties prenantes (T. Leroy, C. Dubois, M. Ruiz, E. Schneider, DPO, SIRH, paie, Finance) et guide d'entretien.

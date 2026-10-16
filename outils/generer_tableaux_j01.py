"""Génère les tableaux du Jalon 1 en Excel et en Markdown à partir d'une seule source.

- 02_Besoins_Metier/J01_NomEquipe_RH_QuestionsClient_V01.xlsx / .md
- 01_Cadrage/J01_NomEquipe_RH_Kanban_V01.xlsx / .md

Modifier les listes QUESTIONS et TACHES ci-dessous, puis relancer :
python outils/generer_tableaux_j01.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EQUIPE = "NomEquipe"

THEMES = {"M": "Métier", "D": "Données", "P": "Processus", "K": "KPI", "S": "Sécurité", "C": "Contraintes"}
PRIORITES = {"P1": "Bloquant : sans réponse, l'indicateur ne peut pas être défini",
             "P2": "Important : nécessaire avant la modélisation (jalon 4)",
             "P3": "Utile : peut attendre ou être couvert par une hypothèse"}

# (ID, priorité, question, pourquoi on la pose, anomalies liées, interlocuteur pressenti, hypothèse de travail)
QUESTIONS = [
    # ------------------------------------------------------------------ Métier
    ("M01", "P1", "Quelle date d'arrêté et quelle période de référence devons-nous utiliser pour toute l'analyse ?",
     "Les 4 mails datent du 13/01/2025, mais la paie, les absences et les recrutements couvrent toute l'année "
     "2025. Le nombre de certifications expirées passe de 218 à 440 selon la date retenue.",
     "A069, A130–A134", "Direction RH groupe", "Arrêté au 31/12/2025, période 01/01–31/12/2025"),
    ("M02", "P1", "Qui arbitre entre définitions groupe et définitions locales, et qui valide nos propositions ?",
     "La politique RH indique qu'aucune autorité n'est désignée. Sans valideur, aucune définition ne sera "
     "gouvernée.", "A113", "Direction RH groupe", "Le demandeur de chaque mail valide son indicateur"),
    ("M03", "P1", "Quelle population compose l'effectif présenté au COMEX : personnes physiques, contrats actifs, "
     "salariés payés ou ETP ? Faut-il inclure les absences longues, CDD, alternants, externes et sortis encore payés ?",
     "Selon la lecture, l'effectif va de 655 à 800. Les catégories alternant et externe n'existent pas dans les "
     "données ; l'ETP est incalculable sans temps contractuel.", "A004, A006, A013, A112, A129",
     "T. Leroy", "Personnes physiques sous contrat actif, absences longues incluses, à une date d'arrêté"),
    ("M04", "P1", "Comment calculer le turnover : mobilités internes, fins de CDD et départs en période d'essai "
     "inclus ou non ? Sur quel effectif de référence ? Comment ont été obtenus 35 %, 22 % et 18 % ?",
     "Le référentiel ne compte que 7 sorties datées en 2025, sans motif ni historique : aucun des trois chiffres "
     "ne peut en être tiré.", "A126", "C. Dubois, comité Sales, Finance",
     "Départs externes / effectif moyen, hors mobilités internes"),
    ("M05", "P1", "Quel périmètre pour la masse salariale (brut, bonus, bonus différés, charges employeur, "
     "expatriés) et quelle méthode de conversion (taux moyen ou de clôture, à quelle date) ?",
     "RH et Finance divergent ; aucune de ces notions n'est présente dans les fichiers et aucun taux de change "
     "n'est fourni.", "A120, A127, A137", "M. Ruiz, Finance", "Brut + bonus, hors charges, taux moyen mensuel"),
    ("M06", "P1", "Quelles formations sont obligatoires, pour quels sites et quels postes ? Quelle source fait "
     "foi entre le LMS, l'Excel local et le prestataire ?",
     "Les 7 formations sont tantôt obligatoires, tantôt optionnelles ; 264 lignes sans caractère obligatoire ; "
     "aucun poste dans les données.", "A064, A065, A072, A128, A135", "E. Schneider",
     "Safety L1 et Forklift obligatoires pour tous ; le LMS fait foi"),
    ("M07", "P2", "Le dossier ne contient ni onboarding, ni tickets RH, ni règles d'accès RGPD, ni mail du "
     "directeur RH annoncés au cahier des charges : existent-ils ? Le prototype attendu reste-t-il le même ?",
     "Les indicateurs onboarding et tickets RH n'ont aucune source.", "A136", "Enseignante (client)",
     "Prototype centré sur effectif, absentéisme, formations et recrutement"),
    ("M08", "P2", "Qui utilisera le tableau de bord RH (COMEX, DRH, RH pays, managers), pour quelles décisions et "
     "à quelle fréquence ?", "Conditionne le niveau de détail, les droits d'accès et le rafraîchissement.",
     "—", "Direction RH groupe", "COMEX mensuel agrégé ; RH pays avec détail de leur périmètre"),
    ("M09", "P3", "Quelle version du guide de rémunération fait foi (bonus G7 à 8 % ou 10 %) et comment les "
     "bandes locales correspondent-elles aux grades G5–G10 ?", "Deux versions circulent.",
     "A119, A121, A122", "Compensation & Benefits", "Grades G5–G10 seuls, sans bonus cible"),
    # ------------------------------------------------------------------ Données
    ("D01", "P1", "Pouvez-vous fournir les fiches des 10 matricules EMP-00761 à EMP-00770 ?",
     "Absents du référentiel, ils sont payés et présents dans l'organigramme : leurs lignes ont été écrasées "
     "par des doublons (EMP-00101 à EMP-00110).", "A001, A002, A019, A096", "SIRH",
     "Reconstituer leurs attributs depuis l'organigramme"),
    ("D02", "P1", "Que désignent les 22 identifiants EXT-xxxx de la paie ?",
     "Ils occupent exactement les lignes des 22 salariés du référentiel sans paie (EXT-0000 ↔ EMP-00001, "
     "EXT-0037 ↔ EMP-00038…) : externes ou matricules écrasés à l'export ?", "A018", "Service paie",
     "Matricules écrasés : EXT-n ↔ EMP-(n+1), à confirmer"),
    ("D03", "P1", "Pouvez-vous fournir l'extraction complète de la paie 2025 (12 mois) ? Les fichiers sont-ils "
     "des extraits ?", "Un seul mois par salarié ; les 9 fichiers font tous exactement 800 lignes ; moins de "
     "2 pointages par salarié sur l'année.", "A017, A044, A142", "Service paie, SIRH",
     "Travailler sur l'échantillon, sans extrapoler de total annuel"),
    ("D04", "P1", "Dans quelle devise sont réellement exprimés les montants de paie, et quelle source fait foi "
     "entre la paie et le référentiel ? Pouvez-vous fournir les taux de change 2025 ?",
     "Les montants tournent autour de 5 000 quelle que soit la devise ; 31 devises vides ; 555 lignes où la "
     "devise diffère du référentiel ; 603 lignes du référentiel avec une devise incohérente avec le pays.",
     "A014, A021–A024, A137", "Service paie, Finance", "Devise déduite du pays du salarié"),
    ("D05", "P1", "Entre le référentiel salariés et l'organigramme, quelle source fait foi pour le département, "
     "le pays et le manager ?", "Les deux fichiers se contredisent pour 682 départements sur 790, 656 pays et "
     "765 managers.", "A088–A090", "SIRH", "Le référentiel salariés fait foi"),
    ("D06", "P2", "Les 9 salaires bruts négatifs sont-ils des régularisations ou des erreurs de signe ?",
     "Le coût employeur reste positif et cohérent avec la valeur absolue.", "A020", "Service paie",
     "Erreur de signe : valeur absolue"),
    ("D07", "P2", "Les 15 salariés « actifs » sortis le 31/12/2024 sont-ils partis ? Les 20 inactifs avec une "
     "sortie entre 2026 et 2031 ont-ils une sortie programmée ?", "Effectif, turnover et paie après sortie en "
     "dépendent.", "A004, A005, A027", "SIRH", "Date de sortie passée ⇒ inactif"),
    ("D08", "P2", "Quelle est l'unité réelle des absences notées « Hours » ? Les durées sont-elles en jours "
     "calendaires ou ouvrés ?", "Pour 265 absences sur 268 en « Hours », la durée égale le nombre de jours "
     "entre début et fin.", "A048–A050", "Gestion des temps", "Toutes les durées sont en jours calendaires"),
    ("D09", "P2", "Quel est le format de date de chaque source de pointage (Badge, Import, Manual) ?",
     "215 dates sont ambiguës entre jour et mois.", "A033, A034", "Gestion des temps",
     "Dates ambiguës écartées des calculs"),
    ("D10", "P2", "« CDI » et « Permanent » sont-ils le même contrat ? Que recouvre « Local contract » ?",
     "Ces deux points touchent 380 lignes du référentiel.", "A011, A012", "SIRH", "CDI = Permanent ; Local contract = CDI local"),
    ("D11", "P2", "Pouvez-vous fournir les référentiels manquants : centres de coût, approbateurs MGR-xxx avec "
     "leur matricule, managers EMP-900xx et EMP-99999 ?", "Sans eux, absences et paie ne se rattachent ni aux "
     "managers ni à Finance.", "A009, A031, A056, A091, A138", "SIRH, contrôle de gestion", "Analyses par "
     "manager reportées"),
    ("D12", "P3", "Comment lire la matrice de compétences : correspondance entre niveaux 1–5 et libellés "
     "Beginner–Expert, et quelle évaluation retenir en cas de doublon ?", "Le libellé ne suit aucun des deux "
     "niveaux ; 47 doublons.", "A098, A102", "RH développement", "Niveau manager, évaluation la plus récente"),
    ("D13", "P3", "Quelle est la période et la population de l'enquête d'engagement ?",
     "6 sites sur 7 comptent plus de répondants que de salariés actifs (Madrid 144 %).", "A106, A111",
     "RH groupe", "Résultats présentés sans taux de participation"),
    ("D14", "P3", "Que mesurent les compteurs des onglets « Vue synthèse » (47 anomalies connues, 14 budgets "
     "incohérents, 17 chaînes à investiguer, 14 certifications à revoir) ?",
     "Nous ne retrouvons pas ces chiffres : par exemple 51 embauches sur budget non approuvé au lieu de 14.",
     "A141", "Auteurs des fichiers", "Compteurs ignorés"),
    ("D15", "P3", "Une même formation suivie plusieurs fois correspond-elle à un renouvellement ? Quelle est la "
     "durée de validité de chaque formation ?", "Validités de 1, 2 ou 3 ans pour une même formation ; 52 "
     "répétitions.", "A068, A071", "Formation", "La réalisation la plus récente fait foi"),
    # ------------------------------------------------------------------ Processus
    ("P01", "P2", "Quand le statut passe-t-il à Inactive et quand la paie s'arrête-t-elle à la sortie ?",
     "56 paies versées après la sortie, 67 pointages et 68 absences après la sortie.", "A027, A041, A059",
     "SIRH, paie", "Une paie après sortie est une régularisation, isolée dans un indicateur dédié"),
    ("P02", "P2", "Qui est le Hiring Manager ? Peut-on embaucher sans budget approuvé ? Où est tracé le salarié "
     "embauché ?", "51 embauches sur budget non approuvé ; 636 responsables d'un autre département ; aucun lien "
     "poste → salarié.", "A080, A086, A087", "Recrutement", "Hiring Manager = recruteur RH"),
    ("P03", "P2", "Qui valide les absences ? Les absences Pending et Rejected comptent-elles ? Le télétravail "
     "doit-il sortir du fichier d'absences ?", "138 télétravails saisis en absence ; 27 absences approuvées sans "
     "approbateur.", "A052, A055, A057", "Gestion des temps", "Seules les absences approuvées, hors télétravail"),
    ("P04", "P2", "Qui contrôle les journées de plus de 12 heures, selon quelle procédure ? Existe-t-il des "
     "postes de nuit ?", "La politique exige le contrôle sans le décrire ; 18 sorties avant l'entrée.",
     "A035, A037, A117", "Gestion des temps", "Sortie < entrée = poste de nuit"),
    ("P05", "P3", "Qui maintient l'organigramme, à quelle fréquence, et à quelle date est-il valable ?",
     "Ni date d'effet ni historique ; boucle hiérarchique EMP-00301 → … → EMP-00309.", "A092, A097", "SIRH",
     "Organigramme valable à la date d'arrêté"),
    # ------------------------------------------------------------------ KPI
    ("K01", "P1", "Quels indicateurs attendez-vous en priorité pour la première version du tableau de bord ?",
     "Le cahier des charges cite effectif, turnover, absentéisme, recrutement, onboarding et tickets RH ; les "
     "mails ajoutent masse salariale et conformité.", "—", "Direction RH groupe",
     "Effectif, absentéisme, conformité formations, délai de recrutement"),
    ("K02", "P2", "Quelle formule pour le taux d'absentéisme : jours d'absence sur jours théoriques ? Les congés "
     "payés entrent-ils dans le calcul ?", "Motifs bilingues, unités mélangées, télétravail inclus.",
     "A050–A052", "Direction RH groupe", "Maladie + accident / jours théoriques, hors congés et télétravail"),
    ("K03", "P2", "Le délai de recrutement court-il jusqu'à la clôture ou jusqu'à l'embauche ? Une période "
     "On Hold suspend-elle le délai ?", "209 postes pourvus ou clos sans date de clôture.", "A076, A077",
     "Recrutement", "Ouverture → clôture, On Hold inclus"),
    ("K04", "P3", "Quelle formule pour l'engagement et l'eNPS ?", "Recommandation notée de 0 à 10, autres "
     "scores de 1 à 10.", "A108", "RH groupe", "eNPS standard : % notes 9–10 moins % notes 0–6"),
    ("K05", "P3", "Quel est le score minimal de réussite d'une formation ?", "176 formations réussies avec un "
     "score inférieur à 60.", "A070", "Formation", "Le statut fait foi, pas le score"),
    # ------------------------------------------------------------------ Sécurité
    ("S01", "P1", "Qui peut voir quelles données RH, et à quel niveau d'agrégation pour les rémunérations ?",
     "Les règles d'accès RGPD annoncées n'ont pas été fournies ; la paie est individuelle.", "A032, A136",
     "DPO, direction RH", "Rémunérations visibles uniquement en agrégats"),
    ("S02", "P1", "Quel seuil minimal de masquage des petits groupes appliquer ?",
     "Seuil non précisé par la politique RH ; 255 groupes sur 294 comptent moins de 5 répondants.",
     "A107, A114", "DPO", "Masquage en dessous de 5"),
    ("S03", "P2", "Pouvons-nous conserver la clé anonyme à côté du matricule, ou faut-il isoler la table de "
     "correspondance ?", "La pseudonymisation est aujourd'hui inopérante.", "A016", "DPO",
     "Table de correspondance isolée, accès restreint"),
    ("S04", "P2", "Les données fournies sont-elles fictives ? Pouvons-nous les héberger dans le cloud et sur un "
     "dépôt de code ? Combien de temps les conserver ?", "Le dépôt GitHub de l'équipe est public à ce jour.",
     "—", "Enseignante (client), DPO", "Données fictives ; dépôt passé en privé par précaution"),
    # ------------------------------------------------------------------ Contraintes
    ("C01", "P2", "Quels outils sont imposés ou disponibles (Power BI, Microsoft Fabric, licences) ?",
     "Conditionne l'architecture cible des jalons 4 et 5.", "—", "Enseignante (client), DSI",
     "Power BI Desktop et outils gratuits"),
    ("C02", "P2", "Quand ont lieu le prochain comité Sales et le prochain COMEX ? Sous quel délai pouvez-vous "
     "répondre à nos questions ?", "Fixe l'ordre de traitement des indicateurs.", "—", "Direction RH groupe",
     "Effectif d'abord, puis turnover"),
    ("C03", "P3", "Dans quelle langue et quelle devise présenter les résultats au groupe ?",
     "Libellés en trois langues ; quatre devises.", "A140", "Direction RH groupe", "Français, EUR"),
    ("C04", "P3", "Quels usages de l'IA sont acceptables, sachant qu'aucune décision individuelle ne doit être "
     "automatisée ?", "Contrainte du guide de rémunération, à respecter pour le cas d'usage du jalon 7.",
     "A125", "DPO, direction RH", "Assistant de consultation de règles, sans décision individuelle"),
]

# (ID, tâche, responsable, colonne, date cible, dépend de, blocage, prochaine action, livrable)
TACHES = [
    ("T01", "Constituer l'équipe et répartir les rôles", "Tous", "Terminé", "2026-10-05", "", "",
     "—", "Fiche d'équipe"),
    ("T02", "Déposer les 15 fichiers clients tels quels (data/raw, docs)", "Antoine", "Terminé", "2026-10-16",
     "", "", "—", "data/raw, docs"),
    ("T03", "Créer l'arborescence commune des 12 dossiers dans le dépôt", "Antoine", "Terminé", "2026-10-16",
     "", "", "—", "Dépôt GitHub"),
    ("T04", "Profiler les sources et tenir le registre d'anomalies (script rejouable)", "Antoine", "À valider",
     "2026-10-19", "T02", "", "Relecture par Suzanne", "03_Audit_Donnees"),
    ("T05", "Relire l'audit du point de vue des indicateurs", "Suzanne", "À faire", "2026-10-20", "T04", "",
     "Vérifier chaque constat sur les indicateurs", "Commentaires sur l'analyse"),
    ("T06", "Compléter la matrice indicateurs × sources", "Suzanne", "À valider", "2026-10-20", "T04", "",
     "Relire l'onglet Indicateurs du classeur", "Onglet Indicateurs"),
    ("T07", "Pré-analyse graphique des anomalies (Power BI)", "Suzanne", "À faire", "2026-10-21", "T04", "",
     "Brancher Power BI sur l'onglet Anomalies", "Graphiques pour la restitution"),
    ("T08", "Formuler et prioriser les questions client", "Hugo", "À valider", "2026-10-20", "T04", "",
     "Relire, reformuler et classer avec Alexandre", "02_Besoins_Metier"),
    ("T09", "Questions sécurité, RGPD et contraintes", "Alexandre", "À valider", "2026-10-20", "T04", "",
     "Compléter les thèmes Sécurité et Contraintes", "02_Besoins_Metier"),
    ("T10", "Rédiger la note de compréhension de la mission", "Hugo", "À valider", "2026-10-21", "T08", "",
     "Relecture par les 4 membres", "01_Cadrage"),
    ("T11", "Ouvrir le registre des risques", "Alexandre", "À valider", "2026-10-20", "", "",
     "Revue des probabilités et impacts en équipe", "01_Cadrage"),
    ("T12", "Tenir le journal des décisions", "Antoine", "En cours", "2026-10-23", "", "",
     "Faire valider les décisions du 16/10", "01_Cadrage"),
    ("T13", "Choisir le nom de l'équipe", "Tous", "Bloqué", "2026-10-19", "", "Décision d'équipe en attente",
     "Renommer les fichiers NomEquipe", "Convention de nommage"),
    ("T14", "Choisir l'outil Kanban définitif (GitHub Projects proposé)", "Antoine", "À faire", "2026-10-19",
     "", "", "Proposer en point d'équipe", "Fiche d'équipe"),
    ("T15", "Passer le dépôt GitHub en privé", "Antoine", "À faire", "2026-10-17", "", "",
     "Settings → Danger Zone → Change visibility", "Dépôt GitHub"),
    ("T16", "Envoyer les questions P1 au client", "Hugo", "À faire", "2026-10-21", "T08, T09", "",
     "Valider la liste, puis l'envoyer", "Mail au client"),
    ("T17", "Remplir les journaux individuels de contribution", "Tous", "À faire", "2026-10-22", "", "",
     "Chacun complète ses lignes", "01_Cadrage"),
    ("T18", "Note d'avancement du jalon et checklist avant dépôt", "Antoine", "À faire", "2026-10-22",
     "T04–T17", "", "Cocher la checklist du §11", "01_Cadrage"),
    ("T19", "Préparer la restitution synthétique", "Hugo, Suzanne", "À faire", "2026-10-23", "T07, T16", "",
     "Un résultat, un choix, une difficulté, la prochaine priorité", "12_Soutenance"),
    ("T20", "Exporter les livrables en PDF pour le dépôt", "Antoine", "À faire", "2026-10-23", "T18", "",
     "Exporter les .md en PDF", "Dossier du jalon"),
    ("T21", "Préparer le jalon 2 : cartographie des parties prenantes et guide d'entretien", "Hugo",
     "À faire", "2026-10-26", "T16", "", "Partir des interlocuteurs pressentis", "02_Besoins_Metier"),
]
COLONNES = ["À faire", "En cours", "À valider", "Terminé", "Bloqué"]


def md_table(df: pd.DataFrame) -> str:
    def cell(v):
        return str(v).replace("|", "\\|").replace("\n", " ") if pd.notna(v) and v != "" else "—"
    lignes = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lignes += ["| " + " | ".join(cell(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lignes)


def ecrire_xlsx(path: Path, feuilles: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="xlsxwriter") as xw:
        wrap = xw.book.add_format({"text_wrap": True, "valign": "top"})
        for nom, df in feuilles.items():
            df.to_excel(xw, sheet_name=nom, index=False)
            ws = xw.sheets[nom]
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, len(df), len(df.columns) - 1)
            for i, c in enumerate(df.columns):
                ws.set_column(i, i, max(8, min(60, int(max(df[c].astype(str).str.len().max(), len(c)) * 0.9))), wrap)


# ---------------------------------------------------------------------------- questions
q = pd.DataFrame(QUESTIONS, columns=["ID", "Priorité", "Question", "Pourquoi nous la posons",
                                     "Anomalies liées", "Interlocuteur pressenti",
                                     "Hypothèse de travail si pas de réponse"])
q.insert(1, "Thème", q["ID"].str[0].map(THEMES))
q["Réponse du client"] = ""
q["Date de réponse"] = ""
q["Statut"] = "À envoyer"
ecrire_xlsx(ROOT / "02_Besoins_Metier" / f"J01_{EQUIPE}_RH_QuestionsClient_V01.xlsx", {
    "Questions": q,
    "Légende": pd.DataFrame({"Priorité": list(PRIORITES), "Signification": list(PRIORITES.values())}),
})

compte = q.pivot_table(index="Thème", columns="Priorité", values="ID", aggfunc="count", fill_value=0)
compte = compte.reindex(list(THEMES.values())).reindex(columns=list(PRIORITES), fill_value=0)
compte["Total"] = compte.sum(axis=1)
compte.loc["Total"] = compte.sum()
md = [f"# Questions à poser au client — Jalon 1", "",
      f"Équipe {EQUIPE} · Ressources humaines · V01 du 16/10/2026 · Fichier généré par "
      "`outils/generer_tableaux_j01.py` (version Excel avec colonnes de suivi : "
      f"`J01_{EQUIPE}_RH_QuestionsClient_V01.xlsx`).", "",
      "**Statut : brouillon à relire par Hugo (Business Analyst) et Alexandre (Qualité, Sécurité). "
      "Rien n'a encore été envoyé au client.**", "",
      "Chaque question part d'un constat chiffré de l'audit (colonne « Anomalies liées », identifiants du "
      "registre `03_Audit_Donnees/J01_NomEquipe_RH_AuditDonnees_V01.xlsx`). Elle propose aussi l'hypothèse de "
      "travail que l'équipe retiendra si le client ne répond pas, pour ne jamais rester bloquée. Les questions "
      "portent sur les besoins et les règles, pas sur une solution technique.", "",
      "## Priorités", "", md_table(pd.DataFrame({"Priorité": list(PRIORITES), "Signification": list(PRIORITES.values())})),
      "", md_table(compte.reset_index().astype(str)), "",
      "## Les questions P1 à envoyer en premier", "",
      "Ces " + str((q["Priorité"] == "P1").sum()) + " questions conditionnent les quatre indicateurs demandés "
      "dans les mails (effectif, masse salariale, turnover, conformité) et la sécurité des données.", "",
      md_table(q[q["Priorité"] == "P1"][["ID", "Thème", "Question", "Interlocuteur pressenti"]]), ""]
for lettre, theme in THEMES.items():
    sous = q[q["ID"].str[0] == lettre]
    md += [f"## {theme}", "", md_table(sous[["ID", "Priorité", "Question", "Pourquoi nous la posons",
                                             "Anomalies liées", "Interlocuteur pressenti",
                                             "Hypothèse de travail si pas de réponse"]]), ""]
(ROOT / "02_Besoins_Metier" / f"J01_{EQUIPE}_RH_QuestionsClient_V01.md").write_text("\n".join(md), encoding="utf-8")

# ---------------------------------------------------------------------------- kanban
k = pd.DataFrame(TACHES, columns=["ID", "Tâche", "Responsable", "Colonne", "Date cible", "Dépend de",
                                  "Blocage", "Prochaine action", "Livrable"])
ecrire_xlsx(ROOT / "01_Cadrage" / f"J01_{EQUIPE}_RH_Kanban_V01.xlsx", {
    "Kanban": k,
    "Charge": k.assign(Responsable=k["Responsable"].str.split(", ")).explode("Responsable")
    .pivot_table(index="Responsable", columns="Colonne", values="ID", aggfunc="count", fill_value=0)
    .reindex(columns=COLONNES, fill_value=0).reset_index(),
})
md = [f"# Kanban initial — Jalon 1", "",
      f"Équipe {EQUIPE} · Ressources humaines · état au 16/10/2026 · Fichier généré par "
      f"`outils/generer_tableaux_j01.py` (export Excel : `J01_{EQUIPE}_RH_Kanban_V01.xlsx`).", "",
      "Colonnes imposées par le sujet : À faire, En cours, À valider, Terminé, Bloqué. Les dates cibles sont "
      "provisoires et seront recalées sur la date de remise annoncée par l'enseignante. L'outil Kanban "
      "définitif reste à choisir (tâche T14) : ce fichier sert de point de départ et peut être importé dans "
      "GitHub Projects ou Trello.", "",
      md_table(k.assign(Responsable=k["Responsable"].str.split(", ")).explode("Responsable")
               .pivot_table(index="Responsable", columns="Colonne", values="ID", aggfunc="count", fill_value=0)
               .reindex(columns=COLONNES, fill_value=0).reset_index().astype(str)), ""]
for col in COLONNES:
    sous = k[k["Colonne"] == col]
    md += [f"## {col} ({len(sous)})", "",
           md_table(sous[["ID", "Tâche", "Responsable", "Date cible", "Dépend de", "Blocage", "Prochaine action"]])
           if len(sous) else "_Aucune tâche._", ""]
(ROOT / "01_Cadrage" / f"J01_{EQUIPE}_RH_Kanban_V01.md").write_text("\n".join(md), encoding="utf-8")
print(f"{len(q)} questions, {len(k)} tâches générées")

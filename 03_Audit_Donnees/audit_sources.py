"""Audit initial des sources RH — Jalon 1.

Lit les fichiers clients en lecture seule (data/raw et docs/) et produit le
classeur J01_NomEquipe_RH_AuditDonnees_V01.xlsx dans le même dossier.
Aucune donnée n'est corrigée : les interprétations (formats de date,
synonymes) ne servent qu'à mesurer les anomalies.

Usage : python 03_Audit_Donnees/audit_sources.py
"""
from __future__ import annotations

import email
import hashlib
import re
from email import policy
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MAILS = ROOT / "docs" / "mails"
REFS = ROOT / "docs" / "referentiels"
OUT = Path(__file__).resolve().parent / "J01_NomEquipe_RH_AuditDonnees_V01.xlsx"

# Dates de référence provisoires : la date des 4 mails et la fin de la période de paie.
REF_MAILS = pd.Timestamp("2025-01-13")
REF_FIN = pd.Timestamp("2025-12-31")
DEVISE_PAYS = {"France": "EUR", "Espagne": "EUR", "Allemagne": "EUR",
               "Chili": "CLP", "Chine": "CNY", "Pologne": "PLN"}
FANTOMES = [f"EMP-{i:05d}" for i in range(761, 771)]


# --------------------------------------------------------------------------- chargement
def lire_csv(nom: str, sep: str) -> pd.DataFrame:
    return pd.read_csv(RAW / nom, sep=sep, dtype=str, encoding="utf-8-sig",
                       keep_default_na=False, na_values=[""])


def lire_xlsx(nom: str) -> pd.DataFrame:
    df = pd.read_excel(RAW / nom, sheet_name=0, dtype=object)
    return df.apply(lambda s: s.map(lambda v: v if pd.isna(v) else str(v)))


def lire_synthese(nom: str) -> dict:
    vue = pd.read_excel(RAW / nom, sheet_name="Vue synthèse", header=None)
    return {str(r[0]): r[1] for r in vue.itertuples(index=False) if pd.notna(r[0]) and pd.notna(r[1])
            and r[0] != "Indicateur"}


def date(s: pd.Series, fmt: str) -> pd.Series:
    return pd.to_datetime(s, format=fmt, errors="coerce")


def heure(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, format="%H:%M", errors="coerce")


def lire_mail(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        m = email.message_from_file(f, policy=policy.default)
    return {"De": m["From"], "A": m["To"], "Date": m["Date"], "Objet": m["Subject"],
            "Corps": m.get_body().get_content().strip()}


def lire_pdf(path: Path) -> str:
    from pypdf import PdfReader
    return "\n".join(p.extract_text() for p in PdfReader(path).pages)


E = lire_xlsx("01_Employees_Master.xlsx")
P = lire_csv("02_Payroll_2025.csv", ";")
T = lire_csv("03_Time_Tracking.csv", ",")
A = lire_csv("04_Absenteeism.csv", ";")
F = lire_xlsx("05_Training_History.xlsx")
R = lire_xlsx("06_Recruitment_Pipeline.xlsx")
O = lire_xlsx("07_Organization_Chart.xlsx")
C = lire_xlsx("08_Skills_Matrix.xlsx")
V = lire_csv("09_Employee_Survey.csv", ",")
DATA = {"S01": E, "S02": P, "S03": T, "S04": A, "S05": F, "S06": R, "S07": O, "S08": C, "S09": V}
CLE = {"S01": "Employee_ID", "S02": "Payroll_Row", "S03": "Time_ID", "S04": "Absence_ID",
       "S05": "Training_ID", "S06": "Requisition_ID", "S07": "Employee_ID", "S08": "Skill_Row",
       "S09": "Response_ID"}

# Référentiel dédoublonné, utilisé pour tous les croisements.
EM = E.drop_duplicates("Employee_ID").set_index("Employee_ID")
IDS = set(EM.index)
STATUT = EM["HR_Status"].str.upper().replace({"ACTIF": "ACTIVE"})
SORTIE = date(EM["Termination_Date"], "%Y-%m-%d")
EMBAUCHE = date(EM["Hire_Date"], "%d/%m/%Y")

# --------------------------------------------------------------------------- registre
ANOMALIES: list[dict] = []
MASQUES: dict[str, list[pd.Series]] = {k: [] for k in DATA}


def ajoute(src, colonnes, dimension, constat, volume, base, impact, criticite,
           indicateurs="", client="Oui", piste="", exemples="", masque=None, score=True):
    """Enregistre une anomalie.

    `masque` (booléen aligné sur la source) donne le volume et alimente le score qualité :
    une ligne n'est pas exploitable si une anomalie haute ou moyenne, qui attend une réponse
    du client, la touche. Les règles manquantes et les constats de sécurité portent sur la
    colonne entière, pas sur la ligne : ils n'entrent pas dans le score.
    """
    if masque is not None:
        masque = masque.fillna(False).astype(bool)
        volume = int(masque.sum())
        if not exemples:
            exemples = ", ".join(DATA[src].loc[masque, CLE[src]].astype(str).head(3))
        if (score and criticite in ("Haute", "Moyenne") and client == "Oui"
                and dimension not in ("Règle de gestion manquante", "Sécurité")):
            MASQUES[src].append(masque)
    if volume == 0:
        return
    ANOMALIES.append({
        "Source": src, "Colonne(s)": colonnes, "Dimension qualité": dimension, "Constat": constat,
        "Volume": volume, "Base": base,
        "% de la base": round(100 * volume / base, 1) if isinstance(base, (int, np.integer)) and base else None,
        "Exemples": exemples, "Impact métier": impact, "Criticité": criticite,
        "Indicateurs impactés": indicateurs, "Réponse client requise": client,
        "Piste de correction (non appliquée)": piste,
    })


def ids_absents(serie: pd.Series) -> pd.Series:
    return serie.notna() & ~serie.isin(IDS)


# =========================================================================== S01 référentiel
n = len(E)
ajoute("S01", "toutes", "Unicité",
       "Lignes en double strict : EMP-00101 à EMP-00110 recopiés en fin de fichier (lignes 762 à 771)",
       None, n, "Effectif surestimé de 10 personnes si les lignes sont comptées", "Haute",
       "Effectif, ETP, turnover", "Non", "Dédoublonner sur Employee_ID après vérification",
       masque=E.duplicated(keep="first"))
ajoute("S01", "Employee_ID", "Complétude",
       "Matricules EMP-00761 à EMP-00770 absents du référentiel alors qu'ils figurent dans la paie, "
       "l'organigramme et d'autres sources : les doublons occupent exactement leurs lignes",
       10, len(IDS), "10 salariés payés invisibles dans l'effectif ; cause probable d'une partie de "
       "l'écart RH / Finance (mail M. Ruiz)", "Haute", "Effectif, masse salariale",
       piste="Demander au client les 10 fiches manquantes", exemples="EMP-00761, EMP-00762, EMP-00763")
ajoute("S01", "HR_Status", "Validité",
       "Statut actif écrit de 3 façons (Active, Actif, ACTIVE)", None, n,
       "Un filtre sur « Active » oublie 128 salariés", "Moyenne", "Effectif",
       "Non", "Table de correspondance des statuts",
       masque=E["HR_Status"].isin(["Actif", "ACTIVE"]))
st = E["HR_Status"].str.upper().replace({"ACTIF": "ACTIVE"})
sortie = date(E["Termination_Date"], "%Y-%m-%d")
ajoute("S01", "HR_Status, Termination_Date", "Cohérence",
       "Salariés au statut actif avec une date de sortie (toutes au 31/12/2024)", None, n,
       "Sortis mais encore comptés et payés en 2025 : effectif et masse salariale faussés", "Haute",
       "Effectif, turnover, masse salariale", piste="Faire confirmer la sortie ; règle : date de sortie "
       "passée ⇒ inactif", masque=(st == "ACTIVE") & sortie.notna())
ajoute("S01", "Termination_Date", "Validité",
       "Salariés inactifs avec une date de sortie future (après le 31/12/2025, jusqu'en 2031)",
       None, n, "Sorties programmées ou erreurs de saisie : le turnover 2025 dépend de cette lecture",
       "Moyenne", "Turnover", masque=(st == "INACTIVE") & (sortie > REF_FIN))
ajoute("S01", "HR_Status", "Règle de gestion manquante",
       "Statut « Leave » (absence longue) sans règle d'inclusion dans l'effectif ; la politique RH "
       "et une note locale se contredisent", None, n,
       "Écart de 57 personnes selon la définition retenue", "Moyenne", "Effectif",
       masque=E["HR_Status"].eq("Leave"))
ajoute("S01", "Department", "Complétude",
       "Département vide, sur un bloc contigu EMP-00651 à EMP-00660", None, n,
       "Ces salariés disparaissent des analyses par département", "Moyenne",
       "Effectif par département", masque=E["Department"].isna())
ajoute("S01", "Manager_ID", "Complétude", "Manager vide", None, n,
       "Rattachement hiérarchique inconnu (dirigeants ou oubli ?)", "Basse", "Analyses par manager",
       masque=E["Manager_ID"].isna())
ajoute("S01", "Manager_ID", "Intégrité référentielle",
       "Manager inconnu du référentiel : EMP-90000 à EMP-90011 (12) et EMP-00770 (matricule manquant)",
       None, n, "Chaîne hiérarchique cassée", "Moyenne", "Analyses par manager",
       masque=ids_absents(E["Manager_ID"]))
ajoute("S01", "Manager_ID", "Cohérence", "Salariés rattachés à un manager au statut Inactive", None, n,
       "Organisation non mise à jour après les départs", "Moyenne", "Analyses par manager",
       masque=E["Manager_ID"].map(STATUT).eq("INACTIVE"))
ajoute("S01", "Contract_Type", "Validité",
       "Synonymes « CDI » et « Permanent » pour le même type de contrat", None, n,
       "Répartition par contrat fausse sans regroupement", "Moyenne", "Effectif par contrat", "Non",
       "Table de correspondance des contrats", masque=E["Contract_Type"].eq("CDI"))
ajoute("S01", "Contract_Type", "Règle de gestion manquante",
       "Type « Local contract » non défini (permanent ou temporaire ?)", None, n,
       "Impossible de classer ces salariés en CDI / CDD", "Moyenne", "Effectif par contrat",
       masque=E["Contract_Type"].eq("Local contract"))
ajoute("S01", "Contract_Type", "Complétude",
       "Aucune catégorie alternant, stagiaire ou externe, alors que le mail COMEX les cite", 4, 4,
       "Définition gouvernée de l'effectif impossible à appliquer", "Haute", "Effectif, ETP",
       piste="Obtenir la liste des catégories de population", exemples="Permanent, CDI, Fixed term, Local contract")
ajoute("S01", "Payroll_Currency", "Cohérence",
       "Devise de paie incohérente avec le pays (ex. Allemagne payée en CLP ou CNY)", None, n,
       "Conversion impossible à fiabiliser ; masse salariale faussée", "Haute", "Masse salariale",
       piste="Faire confirmer la devise par pays",
       masque=E["Payroll_Currency"] != E["Country"].map(DEVISE_PAYS))
ajoute("S01", "Hire_Date", "Cohérence temporelle",
       "Embauches postérieures au 13/01/2025, date des mails du client", None, n,
       "La date d'arrêté du fichier est inconnue", "Basse", "Effectif à date",
       masque=date(E["Hire_Date"], "%d/%m/%Y") > REF_MAILS)
ajoute("S01", "Employee_ID, Anonymous_Key", "Sécurité",
       "La clé « anonyme » est stockée à côté du matricule : la pseudonymisation est inopérante",
       len(IDS), len(IDS), "Risque RGPD si le fichier circule tel quel", "Moyenne", "",
       piste="Séparer la table de correspondance et restreindre son accès", exemples="ANON-758744 ↔ EMP-00001")

# =========================================================================== S02 paie
n = len(P)
for c in ["Month", "Gross_Salary", "Bonus", "Overtime_Hours", "Employer_Cost"]:
    P[c + "_n"] = pd.to_numeric(P[c])
paie_emp = P["Employee_ID"].str.startswith("EMP")
ajoute("S02", "Employee_ID, Month", "Complétude",
       f"Une seule ligne de paie par salarié pour toute l'année ({P['Employee_ID'].nunique()} matricules, "
       "800 lignes, 1 mois chacun) au lieu de 12 mois", 800, 800,
       "Masse salariale annuelle incalculable ; le fichier ressemble à un extrait", "Haute",
       "Masse salariale, coût employeur", piste="Demander l'extraction des 12 mois", exemples="PAY-00001 : juillet seul")
ext = P["Employee_ID"].str.startswith("EXT")
manquants = sorted(IDS - set(P["Employee_ID"]))
ajoute("S02", "Employee_ID", "Intégrité référentielle",
       "Identifiants EXT-xxxx situés exactement aux lignes des 22 salariés du référentiel absents de la "
       "paie (EXT-0000 en ligne 1 ↔ EMP-00001, EXT-0037 ↔ EMP-00038, etc.) : externes ou matricules écrasés ?",
       None, n, "22 salariés sans paie et 22 paies sans salarié", "Haute", "Masse salariale, effectif payé",
       piste="Faire confirmer la nature des EXT ; ne pas les exclure en silence", masque=ext)
ajoute("S02", "Employee_ID", "Intégrité référentielle",
       "Salariés payés absents du référentiel (EMP-00761 à EMP-00770)", None, n,
       "Exactement le cas signalé par M. Ruiz", "Haute", "Masse salariale",
       masque=paie_emp & ~P["Employee_ID"].isin(IDS))
ajoute("S02", "Gross_Salary", "Validité",
       "Salaire brut négatif alors que le coût employeur reste positif et cohérent avec la valeur absolue",
       None, n, "Erreur de signe ou régularisation ? Total faussé dans les deux cas", "Haute",
       "Masse salariale", piste="Faire qualifier chaque cas (régularisation, erreur)",
       masque=P["Gross_Salary_n"] < 0)
ajoute("S02", "Currency", "Complétude", "Devise vide", None, n,
       "Montant inconvertible", "Haute", "Masse salariale", masque=P["Currency"].isna())
devise_ref = P["Employee_ID"].map(EM["Payroll_Currency"])
ajoute("S02", "Currency", "Cohérence", "Devise de la paie différente de la devise du référentiel",
       None, n, "Deux sources donnent deux devises pour le même salarié", "Haute", "Masse salariale",
       masque=P["Currency"].notna() & devise_ref.notna() & (P["Currency"] != devise_ref))
pays = P["Employee_ID"].map(EM["Country"])
ajoute("S02", "Currency", "Cohérence", "Devise de la paie incohérente avec le pays du salarié", None, n,
       "Ex. salarié chilien payé en EUR", "Moyenne", "Masse salariale",
       masque=P["Currency"].notna() & pays.notna() & (P["Currency"] != pays.map(DEVISE_PAYS)))
moy = P.groupby("Currency")["Gross_Salary_n"].mean().round(0).to_dict()
ajoute("S02", "Gross_Salary, Currency", "Exactitude",
       "Montants du même ordre quelle que soit la devise (moyenne " +
       ", ".join(f"{k} {v:.0f}" for k, v in moy.items()) + ") : 5 000 CLP valent environ 5 €",
       n, n, "La devise réelle des montants est inconnue", "Haute", "Masse salariale",
       piste="Faire confirmer l'unité des montants", exemples="PAY-00002 : 7 081 CLP")
grade = P["Employee_ID"].map(EM["Grade"]).str[1:].astype(float)
corr = round(pd.concat([grade, P["Gross_Salary_n"]], axis=1).corr().iloc[0, 1], 2)
ajoute("S02", "Gross_Salary", "Cohérence",
       f"Salaire sans lien avec le grade (corrélation {corr}), contrairement au guide de rémunération",
       n, n, "Analyses d'équité par grade non significatives", "Moyenne", "Équité salariale",
       exemples="Salaire médian G5 ≈ G10")
ajoute("S02", "Payroll_Status", "Validité",
       "Statuts mêlant français et anglais (PAYE / Paid) et états intermédiaires (Calculated, Adjusted)",
       None, n, "Quels statuts entrent dans la masse salariale ?", "Moyenne", "Masse salariale",
       masque=P["Payroll_Status"].isin(["PAYE", "Calculated", "Adjusted"]))
mois = pd.to_datetime(dict(year=2025, month=P["Month_n"], day=1))
apres_sortie = P["Employee_ID"].map(SORTIE) < mois
ajoute("S02", "Month", "Cohérence",
       "Paie versée après la date de sortie du salarié", None, n,
       "Régularisation légitime ou paiement indu ? La politique RH admet les régularisations",
       "Haute", "Effectif payé, masse salariale", masque=apres_sortie)
ajoute("S02", "Bonus", "Cohérence",
       "Bonus limité à 4 montants fixes (0, 300, 750, 1 500) sans lien avec le grade, alors que le "
       "guide le définit en % par grade", n, n, "Règle de bonus inapplicable", "Basse", "Masse salariale",
       exemples="G7 : 0, 300, 750 ou 1 500")
ratio = P["Employer_Cost_n"] / P["Gross_Salary_n"].abs()
ajoute("S02", "Employer_Cost", "Règle de gestion manquante",
       f"Ratio coût employeur / brut variable de {ratio.min():.2f} à {ratio.max():.2f} sans règle documentée",
       n, n, "Charges employeur non comparables entre pays", "Moyenne", "Coût employeur",
       exemples="PAY-00001 : 1,18 ; PAY-00002 : 1,28")
ajoute("S02", "Overtime_Hours", "Validité", "Plus de 30 heures supplémentaires dans le mois", None, n,
       "Plafond légal ou conventionnel inconnu", "Basse", "Heures supplémentaires",
       masque=P["Overtime_Hours_n"] > 30)
cc = P.assign(dep=P["Employee_ID"].map(EM["Department"])).groupby("Cost_Center")["dep"].nunique()
ajoute("S02", "Cost_Center", "Intégrité référentielle",
       f"{P['Cost_Center'].nunique()} centres de coût sans référentiel ; chacun mélange {cc.min()} à "
       f"{cc.max()} départements", P["Cost_Center"].nunique(), P["Cost_Center"].nunique(),
       "Rapprochement avec Finance impossible par centre de coût", "Moyenne", "Masse salariale",
       piste="Obtenir le référentiel des centres de coût", exemples="CC-033")
ajoute("S02", "Gross_Salary, Bonus", "Sécurité",
       "Rémunérations individuelles en clair, sans règle d'accès fournie", n, n,
       "Données sensibles : accès à restreindre dès le dépôt", "Haute", "",
       piste="Accès limité au binôme data ; agrégats seulement dans les livrables", exemples="toutes les lignes")

# =========================================================================== S03 temps
n = len(T)
iso = T["Work_Date"].str.match(r"^\d{4}-\d{2}-\d{2}$")
parts = T["Work_Date"].where(~iso).str.split("/", expand=True).astype(float)
ajoute("S03", "Work_Date", "Validité",
       "Trois formats de date : AAAA-MM-JJ, JJ/MM/AAAA et MM/JJ/AAAA (179 dates forcément mois en premier)",
       None, n, "Lecture automatique impossible sans règle", "Moyenne", "Heures travaillées",
       "Non", "Lire chaque format explicitement", masque=~iso)
ajoute("S03", "Work_Date", "Exactitude",
       "Dates ambiguës : jour et mois tous deux ≤ 12, impossible de savoir lequel est le jour", None, n,
       "Ces pointages ne peuvent pas être datés avec certitude", "Haute", "Heures travaillées",
       piste="Demander le format d'export par source (Badge, Import, Manual)",
       masque=(~iso) & (parts[0] <= 12) & (parts[1] <= 12))
cin, cout = heure(T["Clock_In"]), heure(T["Clock_Out"])
ajoute("S03", "Clock_In, Clock_Out", "Cohérence", "Heure de sortie antérieure à l'heure d'entrée",
       None, n, "Poste de nuit ou erreur de saisie ?", "Moyenne", "Heures travaillées",
       masque=cout < cin)
ajoute("S03", "Clock_Out", "Complétude", "Heure de sortie vide", None, n,
       "Durée non vérifiable ; Reported_Hours reste pourtant renseigné", "Moyenne", "Heures travaillées",
       masque=cout.isna())
h = pd.to_numeric(T["Reported_Hours"])
ajoute("S03", "Reported_Hours", "Conformité",
       "Journée de plus de 12 heures (seuil de contrôle de la politique RH)", None, n,
       "Contrôle exigé mais aucune procédure groupe ; 10 de ces journées ont une sortie avant l'entrée",
       "Moyenne", "Journées > 12 h", masque=h > 12)
ajoute("S03", "Work_Mode", "Complétude", "Mode de travail vide", None, n,
       "Taux de télétravail sous-estimé", "Moyenne", "Taux de télétravail", masque=T["Work_Mode"].isna())
ajoute("S03", "Work_Mode", "Validité", "Synonymes Remote / Home et Site / Office", None, n,
       "Quatre valeurs pour deux modes", "Moyenne", "Taux de télétravail", "Non",
       "Table de correspondance des modes", masque=T["Work_Mode"].isin(["Home", "Office"]))
ajoute("S03", "Employee_ID", "Intégrité référentielle", "Matricules absents du référentiel", None, n,
       "Voir S01 : matricules manquants", "Basse", "", "Non", masque=~T["Employee_ID"].isin(IDS))
jour = date(T["Work_Date"], "%Y-%m-%d").fillna(date(T["Work_Date"], "%d/%m/%Y")).fillna(
    date(T["Work_Date"], "%m/%d/%Y"))
ajoute("S03", "Work_Date", "Cohérence", "Pointage après la date de sortie du salarié", None, n,
       "Salarié sorti qui pointe encore", "Moyenne", "Heures travaillées",
       masque=jour > T["Employee_ID"].map(SORTIE))
ajoute("S03", "Work_Date", "Cohérence", "Pointage avant la date d'embauche", None, n,
       "Date d'embauche ou date de pointage erronée", "Basse", "Heures travaillées",
       masque=jour < T["Employee_ID"].map(EMBAUCHE))
ajoute("S03", "Employee_ID, Work_Date", "Unicité", "Deux pointages le même jour pour le même salarié",
       None, n, "Heures comptées deux fois", "Basse", "Heures travaillées", "Non",
       masque=T.assign(j=jour).duplicated(["Employee_ID", "j"], keep="first"))
ajoute("S03", "toutes", "Complétude",
       f"{n} pointages pour {T['Employee_ID'].nunique()} salariés sur toute l'année 2025 "
       "(moins de 2 jours par salarié)", n, n,
       "Échantillon, pas un suivi exhaustif : aucun total d'heures annuel possible", "Moyenne",
       "Heures travaillées, ETP", piste="Demander s'il s'agit d'un extrait", exemples="EMP-00799 : 5 jours")
ajoute("S03", "Source", "Exactitude", "Pointages saisis manuellement", None, n,
       "Fiabilité moindre que le badge", "Basse", "Heures travaillées", "Non",
       masque=T["Source"].eq("Manual"))

# =========================================================================== S04 absences
n = len(A)
deb, fin = date(A["Start_Date"], "%d/%m/%Y"), date(A["End_Date"], "%Y-%m-%d")
duree = pd.to_numeric(A["Duration"])
ajoute("S04", "Start_Date, End_Date", "Validité",
       "Début au format JJ/MM/AAAA et fin au format AAAA-MM-JJ sur la même ligne", n, n,
       "Risque d'inversion jour/mois au chargement", "Basse", "Absentéisme", "Non",
       "Lire chaque colonne avec son format", exemples="ABS-00001")
ajoute("S04", "Start_Date, End_Date", "Cohérence", "Date de fin antérieure au début (toujours la veille)",
       None, n, "Absence de durée négative", "Moyenne", "Absentéisme", masque=fin < deb)
ajoute("S04", "Unit", "Validité", "Trois unités : Hours, Days et jours", None, n,
       "Durées non additionnables", "Haute", "Absentéisme", masque=A["Unit"].isin(["Hours", "jours"]))
cal = (fin - deb).dt.days + 1
ajoute("S04", "Unit, Duration", "Exactitude",
       "Unité « Hours » alors que la durée égale le nombre de jours calendaires entre début et fin",
       None, n, "L'unité est probablement fausse : ces durées sont des jours", "Haute", "Absentéisme",
       piste="Faire confirmer l'unité réelle", masque=A["Unit"].eq("Hours") & (duree == cal))
ajoute("S04", "Duration", "Règle de gestion manquante",
       "Durées en jours calendaires (week-ends inclus), pas en jours ouvrés", None, n,
       "Le taux d'absentéisme dépend du choix calendaire / ouvré", "Moyenne", "Absentéisme",
       masque=A["Unit"].isin(["Days", "jours"]) & (duree == cal))
ajoute("S04", "Absence_Type", "Validité",
       "Motifs en double français / anglais (Sick / Maladie, Annual Leave / Congé)", None, n,
       "Répartition par motif faussée", "Moyenne", "Absences par motif", "Non",
       "Table de correspondance des motifs", masque=A["Absence_Type"].isin(["Maladie", "Congé"]))
ajoute("S04", "Absence_Type", "Cohérence", "Télétravail (Remote Work) saisi comme une absence", None, n,
       "Absentéisme gonflé ; la politique RH confirme cette pratique locale", "Haute",
       "Absentéisme, télétravail", piste="Exclure le télétravail de l'absentéisme (à valider)",
       masque=A["Absence_Type"].eq("Remote Work"))
ajoute("S04", "Absence_Type", "Règle de gestion manquante",
       "Accident sans distinction travail / trajet / vie privée", None, n,
       "Indicateur sécurité au travail impossible", "Basse", "Absentéisme",
       masque=A["Absence_Type"].eq("Accident"))
ajoute("S04", "Approval_Status", "Validité", "Synonymes Validé / Approved", None, n,
       "Statut d'approbation non filtrable", "Moyenne", "Absentéisme", "Non",
       masque=A["Approval_Status"].eq("Validé"))
ajoute("S04", "Approval_Status", "Règle de gestion manquante",
       "Absences Pending ou Rejected : faut-il les compter ?", None, n,
       "Écart de moitié sur le volume d'absences selon la règle", "Moyenne", "Absentéisme",
       masque=A["Approval_Status"].isin(["Pending", "Rejected"]))
ajoute("S04", "Approved_By", "Intégrité référentielle",
       f"{A['Approved_By'].nunique()} codes approbateurs MGR-xxx sans référentiel ni lien avec les matricules EMP",
       None, n, "Impossible de relier l'absence au manager", "Moyenne", "Absentéisme par manager",
       piste="Obtenir la table MGR-xxx ↔ Employee_ID", masque=A["Approved_By"].notna(), score=False)
ajoute("S04", "Approved_By", "Complétude", "Absence approuvée (Approved / Validé) sans approbateur",
       None, n, "Traçabilité de la validation absente", "Moyenne", "Absentéisme",
       masque=A["Approval_Status"].isin(["Approved", "Validé"]) & A["Approved_By"].isna())
chev = pd.Series(False, index=A.index)
for _, g in A.assign(d=deb, f=fin)[fin >= deb].sort_values("d").groupby("Employee_ID"):
    fin_max = g["f"].cummax().shift()
    chev.loc[g.index[(g["d"] <= fin_max).values]] = True
ajoute("S04", "Start_Date, End_Date", "Cohérence", "Absences qui se chevauchent pour un même salarié",
       None, n, "Jours comptés deux fois", "Moyenne", "Absentéisme", masque=chev)
ajoute("S04", "Start_Date", "Cohérence", "Absence commençant après la date de sortie", None, n,
       "Salarié sorti encore absent", "Moyenne", "Absentéisme",
       masque=deb > A["Employee_ID"].map(SORTIE))
ajoute("S04", "Employee_ID", "Intégrité référentielle", "Matricules absents du référentiel", None, n,
       "Voir S01", "Basse", "", "Non", masque=~A["Employee_ID"].isin(IDS))

# =========================================================================== S05 formation
n = len(F)
compl, expi = date(F["Completion_Date"], "%Y-%m-%d"), date(F["Expiry_Date"], "%d/%m/%Y")
ajoute("S05", "Completion_Date, Expiry_Date", "Validité",
       "Formats de date différents entre réalisation (AAAA-MM-JJ) et expiration (JJ/MM/AAAA)", n, n,
       "Risque d'inversion jour/mois", "Basse", "Conformité formations", "Non", exemples="TRN-00001")
ajoute("S05", "Expiry_Date", "Cohérence", "Expiration antérieure à la réalisation (10 jours avant)",
       None, n, "Certification expirée dès sa délivrance", "Moyenne", "Conformité formations",
       masque=expi < compl)
ajoute("S05", "Expiry_Date", "Complétude", "Date d'expiration vide", None, n,
       "Certification permanente ou oubli ?", "Moyenne", "Conformité formations", masque=expi.isna())
ajoute("S05", "Requirement", "Complétude", "Caractère obligatoire non renseigné", None, n,
       "Conformité incalculable pour ces lignes", "Haute", "Conformité formations",
       masque=F["Requirement"].isna())
mixte = F.groupby("Course")["Requirement"].nunique()
ajoute("S05", "Course, Requirement", "Cohérence",
       f"Les {int((mixte > 1).sum())} formations du catalogue sont tantôt obligatoires, tantôt optionnelles",
       int((mixte > 1).sum()), len(mixte),
       "Le caractère obligatoire dépend du site et du poste, mais ni l'un ni l'autre n'est dans le fichier",
       "Haute", "Conformité formations", piste="Obtenir la matrice formation × site × poste",
       exemples="Safety L1, Forklift, GDPR")
ajoute("S05", "Status", "Validité", "Statuts synonymes Completado / Completed / Passed", None, n,
       "Libellés en espagnol et en anglais", "Moyenne", "Conformité formations", "Non",
       masque=F["Status"].isin(["Completado", "Completed"]))
ajoute("S05", "Status, Completion_Date", "Cohérence", "Statut « In progress » avec une date de réalisation",
       None, n, "Formation terminée ou non ?", "Moyenne", "Conformité formations",
       masque=F["Status"].eq("In progress") & compl.notna())
ajoute("S05", "Expiry_Date", "Règle de gestion manquante",
       "Durée de validité de 1, 2 ou 3 ans pour une même formation", n, n,
       "Règle de validité non documentée", "Moyenne", "Conformité formations",
       exemples="Safety L1 : 365, 730 ou 1 095 jours")
ajoute("S05", "Expiry_Date", "Exactitude",
       "Formations expirées au 13/01/2025 (date des mails) — 440 au 31/12/2025", None, n,
       "Le nombre de non-conformes double selon la date de référence", "Haute", "Conformité formations",
       piste="Fixer la date de référence de l'audit", masque=expi < REF_MAILS)
score = pd.to_numeric(F["Score"])
ajoute("S05", "Score, Status", "Règle de gestion manquante",
       "Formation réussie (Passed / Completed) avec un score inférieur à 60", None, n,
       "Seuil de réussite inconnu", "Basse", "Conformité formations",
       masque=F["Status"].isin(["Passed", "Completed", "Completado"]) & (score < 60))
ajoute("S05", "Employee_ID, Course", "Unicité", "Même formation suivie plusieurs fois par un salarié",
       None, n, "Historique de renouvellement ou doublon ?", "Basse", "Conformité formations",
       masque=F.duplicated(["Employee_ID", "Course"], keep="first"))
ajoute("S05", "Source", "Cohérence",
       "Trois sources (LMS, Local Excel, Provider) sans règle de priorité", n, n,
       "Le mail d'audit oppose le LMS aux autres sources", "Moyenne", "Conformité formations",
       exemples="LMS 265, Local Excel 277, Provider 258")
ajoute("S05", "Employee_ID", "Cohérence", "Formations de salariés inactifs", None, n,
       "À exclure de l'audit de conformité", "Basse", "Conformité formations", "Non",
       masque=F["Employee_ID"].map(STATUT).eq("INACTIVE"))
ajoute("S05", "Employee_ID", "Intégrité référentielle", "Matricules absents du référentiel", None, n,
       "Voir S01", "Basse", "", "Non", masque=~F["Employee_ID"].isin(IDS))

# =========================================================================== S06 recrutement
n = len(R)
ouv, clo = date(R["Open_Date"], "%d/%m/%Y"), date(R["Close_Date"], "%Y-%m-%d")
ajoute("S06", "Recruitment_Status", "Validité", "Statut ouvert écrit OPEN et Open", None, n,
       "Comptage des postes ouverts faussé", "Basse", "Postes ouverts", "Non",
       masque=R["Recruitment_Status"].eq("OPEN"))
ajoute("S06", "Close_Date", "Complétude", "Poste pourvu ou clos sans date de clôture", None, n,
       "Délai de recrutement incalculable", "Moyenne", "Délai de recrutement",
       masque=R["Recruitment_Status"].isin(["Hired", "Closed"]) & clo.isna())
ajoute("S06", "Close_Date", "Cohérence", "Poste ouvert ou en attente avec une date de clôture", None, n,
       "Statut ou date erroné", "Moyenne", "Postes ouverts, délai",
       masque=R["Recruitment_Status"].isin(["Open", "OPEN", "On Hold"]) & clo.notna())
ajoute("S06", "Close_Date", "Validité", "Date de clôture future (après le 31/12/2025)", None, n,
       "Date prévisionnelle ou erreur ?", "Basse", "Délai de recrutement", masque=clo > REF_FIN)
ajoute("S06", "Budget_Status", "Complétude", "Statut budgétaire vide", None, n,
       "Suivi budgétaire impossible", "Moyenne", "Recrutement", masque=R["Budget_Status"].isna())
ajoute("S06", "Budget_Status, Recruitment_Status", "Conformité", "Embauche sur un budget non approuvé",
       None, n, "Non-respect du processus de validation", "Haute", "Recrutement",
       masque=R["Recruitment_Status"].eq("Hired") & R["Budget_Status"].eq("Not approved"))
cand, fina = pd.to_numeric(R["Candidates"]), pd.to_numeric(R["Finalists"])
ajoute("S06", "Candidates, Finalists", "Cohérence", "Plus de finalistes que de candidats", None, n,
       "Taux de conversion supérieur à 100 %", "Moyenne", "Taux de conversion", masque=fina > cand)
ajoute("S06", "Finalists, Recruitment_Status", "Cohérence", "Embauche sans aucun finaliste", None, n,
       "Pipeline incomplet", "Basse", "Taux de conversion",
       masque=R["Recruitment_Status"].eq("Hired") & (fina == 0))
ajoute("S06", "Hiring_Manager_ID", "Complétude", "Poste sans responsable de recrutement", None, n,
       "Difficulté annoncée par le cahier des charges", "Moyenne", "Recrutement",
       masque=R["Hiring_Manager_ID"].isna())
ajoute("S06", "Hiring_Manager_ID", "Intégrité référentielle",
       "Responsable de recrutement absent du référentiel (matricules manquants)", None, n,
       "Voir S01", "Basse", "Recrutement", "Non", masque=ids_absents(R["Hiring_Manager_ID"]))
ajoute("S06", "Hiring_Manager_ID", "Cohérence", "Responsable de recrutement au statut Inactive", None, n,
       "Postes pilotés par des personnes parties", "Moyenne", "Recrutement",
       masque=R["Hiring_Manager_ID"].map(STATUT).eq("INACTIVE"))
ajoute("S06", "Hiring_Manager_ID, Department", "Cohérence",
       "Responsable de recrutement d'un autre département que le poste", None, n,
       "Rôle du responsable à clarifier (RH ou manager opérationnel ?)", "Basse", "Recrutement",
       masque=R["Hiring_Manager_ID"].map(EM["Department"]).notna()
       & (R["Hiring_Manager_ID"].map(EM["Department"]) != R["Department"]))
ajoute("S06", "toutes", "Complétude",
       "Ni site, ni matricule du salarié embauché : impossible de suivre recrutement → onboarding", n, n,
       "Le workflow d'arrivée attendu n'a pas de source", "Moyenne", "Recrutement, onboarding",
       exemples="REQ-00001 Hired sans Employee_ID")

# =========================================================================== S07 organigramme
n = len(O)
J = O.join(EM, on="Employee_ID", rsuffix="_ref")
ajoute("S07", "Department", "Cohérence", "Département différent de celui du référentiel", None, n,
       "Deux organisations concurrentes ; aucune source maître désignée", "Haute",
       "Tous les indicateurs par département", piste="Désigner la source qui fait foi",
       masque=J["Department_ref"].notna() & (J["Department"] != J["Department_ref"]))
ajoute("S07", "Country", "Cohérence", "Pays différent de celui du référentiel", None, n,
       "Ventilation par pays incohérente", "Haute", "Tous les indicateurs par pays",
       masque=J["Country_ref"].notna() & (J["Country"] != J["Country_ref"]))
ajoute("S07", "Manager_ID", "Cohérence", "Manager différent de celui du référentiel", None, n,
       "Hiérarchie inexploitable sans arbitrage", "Haute", "Analyses par manager",
       masque=J["Manager_ID"].notna() & J["Manager_ID_ref"].notna() & (J["Manager_ID"] != J["Manager_ID_ref"]))
ajoute("S07", "Manager_ID", "Intégrité référentielle", "Manager EMP-99999 inexistant (valeur bouche-trou ?)",
       None, n, "Hiérarchie cassée", "Moyenne", "Analyses par manager", masque=O["Manager_ID"].eq("EMP-99999"))
chef = O.set_index("Employee_ID")["Manager_ID"].to_dict()
boucle = set()
for e in chef:
    vus, x = [], e
    while x in chef and x not in vus and pd.notna(x):
        vus.append(x)
        x = chef[x]
    if x in vus:
        boucle |= set(vus[vus.index(x):])
sous_boucle = set()
for e in chef:
    vus, x = set(), e
    while isinstance(x, str) and x in chef and x not in vus:
        if x in boucle:
            sous_boucle.add(e)
            break
        vus.add(x)
        x = chef[x]
ajoute("S07", "Manager_ID", "Cohérence",
       "Boucle hiérarchique : EMP-00301 → EMP-00302 → … → EMP-00309 → EMP-00301 ; "
       f"{len(sous_boucle - boucle)} autres salariés en dépendent", None, n,
       "Aucun sommet hiérarchique ; agrégations par ligne managériale impossibles", "Moyenne",
       "Analyses par manager", masque=O["Employee_ID"].isin(boucle))
ajoute("S07", "Primary_Line", "Validité", "Quatre codages du booléen : Y, Yes, 1, N", None, n,
       "Filtre sur la ligne principale peu fiable", "Basse", "", "Non",
       masque=O["Primary_Line"].isin(["Yes", "1"]))
ajoute("S07", "Primary_Line", "Cohérence",
       "Ligne non principale (N) alors que le salarié n'a aucune autre ligne", None, n,
       "Salarié sans rattachement principal", "Moyenne", "Analyses par manager",
       masque=O["Primary_Line"].eq("N"))
ajoute("S07", "Manager_ID", "Complétude", "Manager vide", None, n, "Rattachement inconnu", "Basse",
       "Analyses par manager", masque=O["Manager_ID"].isna())
ajoute("S07", "Employee_ID", "Intégrité référentielle",
       "Salariés présents dans l'organigramme mais absents du référentiel (EMP-00761 à EMP-00770)", None, n,
       "Confirme que ces 10 personnes existent", "Moyenne", "Effectif", masque=~O["Employee_ID"].isin(IDS))
ajoute("S07", "toutes", "Complétude", "Aucune date d'effet : l'organigramme n'est pas historisé", n, n,
       "Impossible de savoir à quelle date il est valable", "Moyenne", "Analyses par département",
       exemples="—")

# =========================================================================== S08 compétences
n = len(C)
ajoute("S08", "Label, Self_Level, Manager_Level", "Cohérence",
       "Deux échelles sans correspondance : niveaux 1 à 5 et libellés Beginner à Expert (le libellé ne suit "
       "aucun des deux niveaux)", None, n, "Cartographie des compétences non interprétable", "Moyenne",
       "Compétences", masque=C["Label"].notna())
ajoute("S08", "Label", "Complétude", "Libellé de niveau vide", None, n, "—", "Basse", "Compétences", "Non",
       masque=C["Label"].isna())
ajoute("S08", "Evidence_Source", "Complétude", "Source de l'évaluation vide", None, n,
       "Fiabilité de l'évaluation inconnue", "Basse", "Compétences", "Non", masque=C["Evidence_Source"].isna())
ajoute("S08", "Last_Assessed", "Complétude", "Date d'évaluation vide", None, n,
       "Fraîcheur de l'évaluation inconnue", "Basse", "Compétences", "Non", masque=C["Last_Assessed"].isna())
ajoute("S08", "Employee_ID, Skill", "Unicité", "Même compétence évaluée deux fois pour un salarié",
       None, n, "Laquelle retenir ?", "Moyenne", "Compétences",
       masque=C.duplicated(["Employee_ID", "Skill"], keep="first"))
ecart = (pd.to_numeric(C["Self_Level"]) - pd.to_numeric(C["Manager_Level"])).abs()
ajoute("S08", "Self_Level, Manager_Level", "Exactitude", "Écart de 4 points entre auto-évaluation et manager",
       None, n, "Correspond aux 11 « écarts forts » de la vue synthèse", "Basse", "Compétences", "Non",
       masque=ecart >= 3)
ajoute("S08", "Employee_ID", "Intégrité référentielle", "Matricules absents du référentiel", None, n,
       "Voir S01", "Basse", "", "Non", masque=~C["Employee_ID"].isin(IDS))
ajoute("S08", "Employee_ID", "Cohérence", "Compétences de salariés inactifs", None, n,
       "À exclure de la cartographie active", "Basse", "Compétences", "Non",
       masque=C["Employee_ID"].map(STATUT).eq("INACTIVE"))

# =========================================================================== S09 enquête
n = len(V)
actifs = EM[STATUT == "ACTIVE"].groupby("Site").size()
taux = (V.groupby("Site").size() / actifs * 100).round(0)
trop = taux[taux > 100]
ajoute("S09", "Site", "Exactitude",
       "Plus de répondants que de salariés actifs sur " + str(len(trop)) + " sites (" +
       ", ".join(f"{s} {v:.0f} %" for s, v in trop.sort_values(ascending=False).items()) + ")",
       None, n, "Population ou période de l'enquête inconnue ; résultats non représentatifs", "Haute",
       "Engagement, eNPS", piste="Demander la période et la population interrogée",
       masque=V["Site"].isin(trop.index))
grp = V.groupby(["Site", "Department", "Grade"])["Response_ID"].transform("size")
nb_grp = V.groupby(["Site", "Department", "Grade"]).ngroups
petits = (V.groupby(["Site", "Department", "Grade"]).size() < 5).sum()
ajoute("S09", "Site, Department, Grade", "Sécurité",
       f"{petits} groupes site × département × grade sur {nb_grp} comptent moins de 5 répondants",
       None, n, "Risque de réidentification ; seuil de masquage non fixé par la politique RH", "Haute",
       "Engagement", piste="Fixer un seuil de masquage (ex. 5) et agréger", masque=grp < 5)
ajoute("S09", "Recommend_Company", "Validité", "Échelle 0–10 pour la recommandation, 1–10 pour les autres scores",
       n, n, "Comparaison directe des scores impossible", "Basse", "Engagement, eNPS", "Non",
       exemples="Recommend_Company = 0 : 66 réponses")
ajoute("S09", "Language, Free_Comment", "Cohérence",
       "Langue sans lien avec le pays (ex. ZH au Chili) et commentaires toujours en français", None, n,
       "Champ Language inexploitable", "Basse", "", "Non",
       masque=~V["Language"].eq(V["Country"].map({"France": "FR", "Espagne": "ES", "Allemagne": "DE",
                                                     "Chine": "ZH", "Chili": "ES", "Pologne": "EN"})))
ajoute("S09", "Free_Comment", "Complétude",
       "Commentaire vide ; les autres se limitent à 5 phrases types", None, n,
       "Pas de vrai texte libre à analyser", "Basse", "Engagement", "Non", masque=V["Free_Comment"].isna())
ajoute("S09", "toutes", "Complétude", "Aucune date de réponse ni de campagne", n, n,
       "Impossible de suivre l'engagement dans le temps", "Moyenne", "Engagement", exemples="—")

# =========================================================================== documents
DOCS = [
    ("S14", "Effectif actif", "Définition contradictoire : contrat actif inclus, absences longues exclues "
     "par une note locale, paie après sortie admise", "Haute", "Effectif"),
    ("S14", "Gouvernance", "Aucune autorité désignée pour arbitrer définitions groupe et locales", "Haute", "Tous"),
    ("S14", "Confidentialité", "Petits groupes à masquer, seuil non précisé", "Haute", "Engagement, tous"),
    ("S14", "Absences", "Codage différent par site ; télétravail enregistré comme absence", "Haute", "Absentéisme"),
    ("S14", "Télétravail", "Règles par pays (France 2 j, Espagne 3 j, Allemagne accord d'équipe, Chine "
     "restreint) ; définition du jour télétravaillé non harmonisée", "Moyenne", "Télétravail"),
    ("S14", "Temps de travail", "Journée > 12 h à contrôler, aucune procédure groupe", "Moyenne", "Journées > 12 h"),
    ("S14", "Version", "« Version diffusée localement » : ni date, ni numéro de version", "Moyenne", "Tous"),
    ("S15", "Version", "Deux versions locales circulent ; laquelle fait foi ?", "Haute", "Masse salariale"),
    ("S15", "Augmentations", "Ni taux de change ni date de référence", "Haute", "Masse salariale"),
    ("S15", "Bonus", "Bonus cible G7 : 8 % dans une version, 10 % dans l'autre", "Moyenne", "Masse salariale"),
    ("S15", "Grades", "Bandes locales conservées, correspondance avec G5–G10 incomplète", "Moyenne", "Équité"),
    ("S15", "Validation", "Rôle du directeur pays ambigu en cas de dépassement", "Basse", "Masse salariale"),
    ("S15", "Bonus", "Mobilités en cours d'année non traitées", "Basse", "Masse salariale"),
    ("S15", "IA", "Aucune décision individuelle ne doit être automatisée : contrainte pour le cas d'usage IA",
     "Basse", "Cas d'usage IA"),
    ("S10", "Turnover", "Trois chiffres (35 %, 22 %, 18 %) ; ni motif de sortie, ni mobilité interne, ni "
     "période d'essai dans les données", "Haute", "Turnover"),
    ("S11", "Masse salariale", "Expatriés, bonus différés, charges et conversions traités différemment ; "
     "aucune de ces notions n'existe dans les fichiers", "Haute", "Masse salariale"),
    ("S12", "Conformité", "Règle par site et par poste, mais aucun poste dans les données ; LMS et audit "
     "se contredisent", "Haute", "Conformité formations"),
    ("S13", "Effectif", "Quatre valeurs (personnes physiques, contrats actifs, payés, ETP) ; alternants et "
     "externes absents des données, ETP sans temps contractuel", "Haute", "Effectif, ETP"),
]
for src, col, constat, crit, kpi in DOCS:
    ajoute(src, col, "Règle de gestion manquante", constat, 1, 1, "Bloque la définition gouvernée de l'indicateur"
           if crit == "Haute" else "À clarifier avant la modélisation", crit, kpi, exemples="—")
for src in ["S10", "S11", "S12", "S13"]:
    ajoute(src, "Date", "Cohérence temporelle",
           "Mail daté du 13/01/2025 alors que les données couvrent toute l'année 2025", 1, 1,
           "La date d'arrêté de l'analyse est inconnue", "Moyenne", "Tous", exemples="13/01/2025 09:00")

TRANSVERSE = [
    ("Aucune date d'arrêté commune aux fichiers ; mails de janvier 2025, données jusqu'en décembre 2025",
     "Haute", "Tous"),
    ("Aucun référentiel de poste / métier : les règles par poste (formations) sont inapplicables",
     "Haute", "Conformité formations, effectif"),
    ("Sources du cahier des charges non fournies : onboarding, tickets RH, règles d'accès RGPD, mail du "
     "directeur RH ; les fichiers reçus portent d'autres noms que ceux annoncés", "Haute",
     "Onboarding, tickets RH"),
    ("Aucun taux de change fourni", "Haute", "Masse salariale"),
    ("Référentiels absents : centres de coût, managers MGR-xxx, sites", "Moyenne", "Masse salariale, absentéisme"),
    ("Cinq conventions de date différentes selon les fichiers et les colonnes", "Moyenne", "Tous"),
    ("Libellés en français, anglais et espagnol mélangés", "Moyenne", "Tous"),
    ("Onglets « Vue synthèse » aux compteurs non traçables (anomalies connues 47, budget incohérent 14, "
     "chaînes à investiguer 17, certifications à revoir 14)", "Moyenne", "Tous"),
    ("Les 9 fichiers comptent tous exactement 800 lignes : extraits ou exports complets ?", "Basse", "Tous"),
]
for constat, crit, kpi in TRANSVERSE:
    ajoute("TR", "—", "Transverse", constat, 1, 1, "Bloquant pour plusieurs indicateurs" if crit == "Haute"
           else "À traiter dans le modèle commun", crit, kpi, exemples="—")

# --------------------------------------------------------------------------- inventaire
INVENTAIRE = [
    ("S01", "01_Employees_Master.xlsx", "Données", "Référentiel salariés", "1 salarié (en théorie)",
     "Pivot de toutes les analyses : effectif, pays, département, grade, contrat"),
    ("S02", "02_Payroll_2025.csv", "Données", "Paie", "1 salarié × 1 mois", "Masse salariale, coût employeur"),
    ("S03", "03_Time_Tracking.csv", "Données", "Temps de travail", "1 pointage journalier",
     "Heures travaillées, télétravail, journées longues"),
    ("S04", "04_Absenteeism.csv", "Données", "Absences", "1 absence", "Taux d'absentéisme, motifs"),
    ("S05", "05_Training_History.xlsx", "Données", "Formation", "1 salarié × 1 formation",
     "Conformité des certifications"),
    ("S06", "06_Recruitment_Pipeline.xlsx", "Données", "Recrutement", "1 poste à pourvoir",
     "Délais, postes ouverts, conversion"),
    ("S07", "07_Organization_Chart.xlsx", "Données", "Organisation", "1 salarié × 1 lien hiérarchique",
     "Structure, rattachements"),
    ("S08", "08_Skills_Matrix.xlsx", "Données", "Compétences", "1 salarié × 1 compétence",
     "Cartographie des compétences"),
    ("S09", "09_Employee_Survey.csv", "Données", "Engagement", "1 réponse anonyme", "Engagement, eNPS"),
    ("S10", "10_mail_turnover_sales.eml", "Mail", "Besoin : turnover", "—", "Expression de besoin (C. Dubois)"),
    ("S11", "11_mail_payroll_gap.eml", "Mail", "Besoin : masse salariale", "—", "Expression de besoin (M. Ruiz)"),
    ("S12", "12_mail_training_audit.eml", "Mail", "Besoin : conformité formations", "—",
     "Expression de besoin (E. Schneider)"),
    ("S13", "13_mail_comex_headcount.eml", "Mail", "Besoin : effectif COMEX", "—",
     "Expression de besoin (T. Leroy)"),
    ("S14", "14_HR_Policy_GlobalTech.pdf", "PDF", "Politique RH", "—", "Règles RH multi-pays"),
    ("S15", "15_Compensation_Guide_2025.pdf", "PDF", "Rémunération", "—", "Règles de grades et bonus"),
]
FORMAT = {"S01": "xlsx, 2 onglets", "S02": "CSV « ; »", "S03": "CSV « , »", "S04": "CSV « ; »",
          "S05": "xlsx, 2 onglets", "S06": "xlsx, 2 onglets", "S07": "xlsx, 2 onglets",
          "S08": "xlsx, 2 onglets", "S09": "CSV « , »"}


def chemin(src: str, fichier: str) -> Path:
    return RAW / fichier if src in DATA else (MAILS if fichier.endswith(".eml") else REFS) / fichier


reg = pd.DataFrame(ANOMALIES)
reg.insert(0, "ID", [f"A{i:03d}" for i in range(1, len(reg) + 1)])
lignes = []
for src, fichier, typ, dom, grain, util in INVENTAIRE:
    p = chemin(src, fichier)
    sous = reg[reg["Source"] == src]
    if src in DATA:
        df = DATA[src]
        touchees = pd.concat(MASQUES[src], axis=1).any(axis=1).sum() if MASQUES[src] else 0
        saines = round(100 * (1 - touchees / len(df)), 1)
        nl, nc = len(df), len([c for c in df.columns if not c.endswith("_n")])
    else:
        saines, nl, nc = None, None, None
    hautes = int((sous["Criticité"] == "Haute").sum())
    qualite = ("Faible" if hautes >= 3 or (saines is not None and saines < 50) else
               "Moyenne" if hautes >= 1 or (saines is not None and saines < 80) else "Bonne")
    lignes.append({
        "ID": src, "Fichier": fichier, "Type": typ, "Format": FORMAT.get(src, typ), "Domaine": dom,
        "1 ligne =": grain, "Lignes": nl, "Colonnes": nc, "Taille (octets)": p.stat().st_size,
        "SHA-256 (12 car.)": hashlib.sha256(p.read_bytes()).hexdigest()[:12],
        "Utilité supposée": util, "Anomalies": len(sous), "dont hautes": hautes,
        "dont moyennes": int((sous["Criticité"] == "Moyenne").sum()),
        "dont basses": int((sous["Criticité"] == "Basse").sum()),
        "% lignes exploitables sans réponse client": saines, "Qualité apparente": qualite,
    })
inventaire = pd.DataFrame(lignes)

# --------------------------------------------------------------------------- profil des colonnes
def motif(v: str) -> str:
    return re.sub(r"\d", "9", re.sub(r"[A-Za-zÀ-ÿ]", "A", v))


profil = []
for src, df in DATA.items():
    for col in [c for c in df.columns if not c.endswith("_n")]:
        s = df[col]
        nn = int(s.notna().sum())
        num = pd.to_numeric(s, errors="coerce")
        motifs = s.dropna().map(motif).value_counts()
        profil.append({
            "Source": src, "Colonne": col, "Non vides": nn, "Vides": len(s) - nn,
            "% vides": round(100 * (len(s) - nn) / len(s), 1), "Valeurs distinctes": int(s.nunique()),
            "Formats observés": " | ".join(f"{m} ({c})" for m, c in motifs.head(3).items()),
            "Valeurs les plus fréquentes": " | ".join(f"{v} ({c})" for v, c in s.value_counts().head(5).items()),
            "Min": num.min() if num.notna().sum() == nn and nn else None,
            "Max": num.max() if num.notna().sum() == nn and nn else None,
        })
profil = pd.DataFrame(profil)

# --------------------------------------------------------------------------- liens entre fichiers
def lien(src, col, cible_ids, cible, commentaire=""):
    s = DATA[src][col].dropna()
    ok = s.isin(cible_ids)
    orph = sorted(s[~ok].unique())
    return {"Source": src, "Colonne": col, "Cible": cible, "Valeurs renseignées": len(s),
            "Rattachées": int(ok.sum()), "% rattachées": round(100 * ok.mean(), 1),
            "Identifiants orphelins": len(orph), "Exemples d'orphelins": ", ".join(orph[:5]),
            "Commentaire": commentaire}


liens = pd.DataFrame([
    lien("S01", "Manager_ID", IDS, "S01 Employee_ID", "EMP-900xx et EMP-00770"),
    lien("S02", "Employee_ID", IDS, "S01 Employee_ID", "22 EXT + 10 matricules manquants"),
    lien("S03", "Employee_ID", IDS, "S01 Employee_ID"),
    lien("S04", "Employee_ID", IDS, "S01 Employee_ID"),
    lien("S04", "Approved_By", IDS, "S01 Employee_ID", "Codes MGR-xxx : aucun référentiel fourni"),
    lien("S05", "Employee_ID", IDS, "S01 Employee_ID"),
    lien("S06", "Hiring_Manager_ID", IDS, "S01 Employee_ID"),
    lien("S07", "Employee_ID", IDS, "S01 Employee_ID", "Attributs contradictoires, voir anomalies S07"),
    lien("S07", "Manager_ID", IDS, "S01 Employee_ID", "EMP-99999"),
    lien("S08", "Employee_ID", IDS, "S01 Employee_ID"),
    {"Source": "S09", "Colonne": "Site, Department, Grade", "Cible": "S01 (agrégé)",
     "Valeurs renseignées": len(V), "Rattachées": None, "% rattachées": None, "Identifiants orphelins": None,
     "Exemples d'orphelins": "", "Commentaire": "Anonyme par construction : jointure agrégée uniquement"},
    {"Source": "S02", "Colonne": "Cost_Center", "Cible": "Référentiel centres de coût", "Valeurs renseignées": len(P),
     "Rattachées": 0, "% rattachées": 0.0, "Identifiants orphelins": P["Cost_Center"].nunique(),
     "Exemples d'orphelins": "CC-001", "Commentaire": "Référentiel non fourni"},
])

# Présence des 10 matricules manquants dans les autres sources
presence = pd.DataFrame({
    "Matricule": FANTOMES,
    **{lib: ["✓" if m in set(df[col]) else "" for m in FANTOMES] for lib, df, col in [
        ("Paie", P, "Employee_ID"), ("Temps", T, "Employee_ID"), ("Absences", A, "Employee_ID"),
        ("Formation", F, "Employee_ID"), ("Recrutement (resp.)", R, "Hiring_Manager_ID"),
        ("Organigramme", O, "Employee_ID"), ("Compétences", C, "Employee_ID"),
        ("Manager dans S01", E, "Manager_ID")]},
})
presence["Nb sources"] = (presence.iloc[:, 1:] == "✓").sum(axis=1)

# --------------------------------------------------------------------------- effectif
actif = STATUT == "ACTIVE"
effectif = pd.DataFrame([
    ("Lignes du référentiel", len(E), "S01", "Contient 10 doublons stricts"),
    ("Matricules uniques du référentiel", len(IDS), "S01", "Tous statuts, sortis compris"),
    ("Personnes connues (référentiel + 10 matricules manquants)", len(IDS) + 10, "S01, S07",
     "Les 10 manquants figurent dans l'organigramme et la paie"),
    ("Statut actif (Active, Actif, ACTIVE)", int(actif.sum()), "S01", "3 graphies regroupées"),
    ("Actifs + absences longues (Leave)", int((actif | (STATUT == "LEAVE")).sum()), "S01",
     "Inclusion de Leave à trancher (politique RH)"),
    ("Actifs sans date de sortie", int((actif & SORTIE.isna()).sum()), "S01",
     "Exclut les 15 « actifs » sortis le 31/12/2024"),
    ("Actifs + Leave, sans sortie, + 10 manquants", int(((actif | (STATUT == "LEAVE")) & SORTIE.isna()).sum()) + 10,
     "S01, S02", "Hypothèse haute de personnes présentes"),
    ("Matricules EMP payés en 2025", int(paie_emp.sum()), "S02", "Dont 10 absents du référentiel"),
    ("Lignes de paie 2025 (EMP + EXT)", len(P), "S02", "22 EXT de nature inconnue"),
    ("ETP", "Non calculable", "—", "Aucun temps de travail contractuel"),
], columns=["Lecture", "Valeur", "Source", "Remarque"])

# --------------------------------------------------------------------------- indicateurs
indicateurs = pd.DataFrame([
    ("Effectif", "Oui", "S01, S02, S07", "Partiellement", "Définition à choisir ; doublons ; 10 manquants ; statuts"),
    ("ETP", "Oui (mail COMEX)", "S01", "Non", "Aucun temps contractuel"),
    ("Taux de turnover", "Oui", "S01", "Non", "7 sorties datées 2025 ; ni motif, ni mobilité, ni historique"),
    ("Taux d'absentéisme", "Oui", "S04, S01", "Non", "3 unités ; télétravail en absence ; jours théoriques inconnus"),
    ("Délai de recrutement", "Oui", "S06", "Partiellement", "209 postes pourvus/clos sans date de clôture"),
    ("Postes ouverts", "Oui", "S06", "Partiellement", "OPEN / Open ; 168 ouverts avec date de clôture"),
    ("Onboarding", "Oui", "—", "Non", "Source non fournie"),
    ("Tickets RH", "Oui", "—", "Non", "Source non fournie"),
    ("Masse salariale / coût employeur", "Non (mail Finance)", "S02", "Non",
     "1 mois par salarié ; devises douteuses ; pas de taux de change"),
    ("Conformité des certifications", "Non (mail audit)", "S05", "Non",
     "Règle par site et poste absente ; date de référence à fixer"),
    ("Répartition par grade / contrat", "Non", "S01", "Partiellement", "Contrats synonymes ; Local contract"),
    ("Ancienneté moyenne", "Non", "S01", "Oui", "Date de référence à fixer"),
    ("Taux de télétravail", "Non", "S03, S04", "Partiellement", "Modes synonymes et vides ; télétravail aussi en absence"),
    ("Journées > 12 h", "Non (politique RH)", "S03", "Oui", "18 pointages sortie < entrée à écarter"),
    ("Taux de conversion candidats → finalistes", "Oui", "S06", "Partiellement", "66 postes > 100 %"),
    ("Écart auto-évaluation / manager", "Non", "S08", "Oui", "47 doublons à arbitrer"),
    ("Engagement / eNPS", "Non", "S09", "Partiellement", "Population et période inconnues ; petits groupes"),
    ("Score de qualité des données", "Non", "Registre", "Oui", "Calculable dès maintenant"),
], columns=["Indicateur", "Cité par le client", "Sources", "Calculable aujourd'hui", "Ce qui bloque"])

# --------------------------------------------------------------------------- documents texte
mails = pd.DataFrame([{"ID": s, "Fichier": f, **lire_mail(MAILS / f)} for s, f, *_ in INVENTAIRE
                      if f.endswith(".eml")])
pdfs = pd.DataFrame([{"ID": s, "Fichier": f, "Texte extrait": lire_pdf(REFS / f)} for s, f, *_ in INVENTAIRE
                     if f.endswith(".pdf")])
vues = pd.DataFrame([{"Fichier": f, "Indicateur": k, "Valeur affichée": v}
                     for _, f, *_ in INVENTAIRE[:9] if f.endswith(".xlsx") for k, v in lire_synthese(f).items()])

synthese = reg.pivot_table(index="Source", columns="Criticité", values="ID", aggfunc="count", fill_value=0)
synthese = synthese.reindex(columns=["Haute", "Moyenne", "Basse"], fill_value=0)
synthese["Total"] = synthese.sum(axis=1)
synthese.loc["Total"] = synthese.sum()
dimensions = reg.pivot_table(index="Dimension qualité", columns="Criticité", values="ID", aggfunc="count",
                             fill_value=0).reindex(columns=["Haute", "Moyenne", "Basse"], fill_value=0)

LISEZ_MOI = pd.DataFrame({"Lisez-moi": [
    "Audit initial des sources RH — Jalon 1 (V01). Généré par 03_Audit_Donnees/audit_sources.py.",
    "Les fichiers clients sont lus en lecture seule : aucune correction n'est appliquée.",
    "Criticité Haute : bloque un indicateur demandé par le client ou crée un risque RGPD.",
    "Criticité Moyenne : fausse un indicateur mais un contournement existe.",
    "Criticité Basse : gêne mineure ou point à documenter.",
    "« % lignes exploitables sans réponse client » = part des lignes touchées par aucune anomalie haute ou "
    "moyenne qui attend une réponse du client (hors règles manquantes et sécurité, qui portent sur la colonne).",
    "Hypothèses de lecture : formats de date lus explicitement par colonne ; Active = Actif = ACTIVE ; "
    "doublons du référentiel ignorés dans les croisements.",
    f"Dates de référence provisoires : {REF_MAILS:%d/%m/%Y} (date des mails) et {REF_FIN:%d/%m/%Y} (fin de la paie).",
    "Devise attendue : EUR pour la France, l'Espagne et l'Allemagne ; CLP, CNY, PLN pour le Chili, la Chine, la Pologne.",
    "Les sources sont numérotées comme les fichiers : S01 = 01_Employees_Master.xlsx, … ; TR = transverse.",
]})

with pd.ExcelWriter(OUT, engine="xlsxwriter") as xw:
    for nom, df, idx in [("Lisez-moi", LISEZ_MOI, False), ("Inventaire_sources", inventaire, False),
                         ("Anomalies", reg, False), ("Synthese", synthese, True),
                         ("Dimensions", dimensions, True), ("Liens", liens, False),
                         ("Matricules_manquants", presence, False), ("Effectif", effectif, False),
                         ("Indicateurs", indicateurs, False), ("Profil_colonnes", profil, False),
                         ("Vues_synthese_client", vues, False), ("Mails", mails, False), ("PDF", pdfs, False)]:
        df.to_excel(xw, sheet_name=nom, index=idx)
        ws = xw.sheets[nom]
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(df), len(df.columns) - (0 if idx else 1))
        largeurs = ([max(10, min(60, df.index.astype(str).str.len().max() + 2))] if idx else []) + [
            max(10, min(70, int(max(df[c].astype(str).str.len().max(), len(str(c))) * 1.1)))
            for c in df.columns]
        wrap = xw.book.add_format({"text_wrap": True, "valign": "top"})
        for i, w in enumerate(largeurs):
            ws.set_column(i, i, w, wrap)

print(f"Classeur écrit : {OUT.relative_to(ROOT)}")
print(f"{len(reg)} anomalies — " + ", ".join(f"{k} {v}" for k, v in reg['Criticité'].value_counts().items()))
print(inventaire[["ID", "Lignes", "Anomalies", "dont hautes", "% lignes exploitables sans réponse client",
                  "Qualité apparente"]].to_string(index=False))
print(effectif.to_string(index=False))

"""Tests du hook `hooks/garde-europa.js` : il demande confirmation avant tout accès
à `D:\\Europa` hors de `5. Memoire IA`, et laisse passer le reste."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "garde-europa.js"
NODE = os.environ.get("NODE") or shutil.which("node") or r"D:\Tools\nodejs\node.exe"
MEMOIRE = r"D:\Europa\5. Memoire IA"


def lancer(tool_name, tool_input, cwd=r"D:\Projets\AI-Harness"):
    entree = {"hook_event_name": "PreToolUse", "cwd": cwd, "tool_name": tool_name, "tool_input": tool_input}
    return subprocess.run([NODE, str(HOOK)], input=json.dumps(entree), capture_output=True, text=True, encoding="utf-8")


def decision(resultat):
    assert resultat.returncode == 0, resultat.stderr
    if not resultat.stdout.strip():
        return None
    return json.loads(resultat.stdout)["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize("chemin", [
    MEMOIRE + r"\_INDEX.md",
    "D:/Europa/5. Memoire IA/Projets/x/x.md",
    MEMOIRE,
    r"D:\Projets\AI-Harness\VISION.md",
    r"D:\Europa-archive\note.md",
])
def test_lecture_autorisee_sans_question(chemin):
    assert decision(lancer("Read", {"file_path": chemin})) is None


@pytest.mark.parametrize("chemin", [
    r"D:\Europa\recherche appartement.md",
    "D:/Europa/1.Projet/note.md",
    r"d:\EUROPA\2. roles\x.md",
    r"D:\Europa",
    r"D:\Europa\5. Memoire IA\..\1.Projet\note.md",
])
def test_lecture_du_coffre_perso_demande_confirmation(chemin):
    assert decision(lancer("Read", {"file_path": chemin})) == "ask"


@pytest.mark.parametrize("outil", ["Write", "Edit"])
def test_ecriture_du_coffre_perso_demande_confirmation(outil):
    assert decision(lancer(outil, {"file_path": r"D:\Europa\note.md"})) == "ask"


def test_notebook_du_coffre_perso_demande_confirmation():
    assert decision(lancer("NotebookEdit", {"notebook_path": r"D:\Europa\carnet.ipynb"})) == "ask"


def test_grep_dans_la_memoire_passe():
    assert decision(lancer("Grep", {"pattern": "x", "path": MEMOIRE})) is None


def test_grep_sur_tout_le_coffre_demande_confirmation():
    assert decision(lancer("Grep", {"pattern": "x", "path": r"D:\Europa"})) == "ask"


def test_grep_sans_chemin_depuis_la_racine_du_disque_demande_confirmation():
    # Sans chemin, Grep cherche dans le dossier courant : depuis D:\ il lirait aussi D:\Europa.
    assert decision(lancer("Grep", {"pattern": "x"}, cwd="D:\\")) == "ask"


def test_grep_sans_chemin_depuis_un_projet_passe():
    assert decision(lancer("Grep", {"pattern": "x"})) is None


def test_glob_avec_motif_absolu_vers_le_coffre_perso_demande_confirmation():
    assert decision(lancer("Glob", {"pattern": "D:/Europa/**/*.md"})) == "ask"


def test_chemin_relatif_resolu_depuis_le_dossier_courant():
    assert decision(lancer("Grep", {"pattern": "x", "path": "1.Projet"}, cwd=r"D:\Europa")) == "ask"
    assert decision(lancer("Grep", {"pattern": "x", "path": "Projets"}, cwd=MEMOIRE)) is None


@pytest.mark.parametrize("outil, commande", [
    ("PowerShell", r'Get-Content "D:\Europa\5. Memoire IA\_INDEX.md"'),
    ("PowerShell", r'git -C "D:\Europa\5. Memoire IA" log --oneline -3'),
    ("Bash", "git -C '/d/Europa/5. Memoire IA' status"),
    ("Bash", r"ls D:/Europa/5.\ Memoire\ IA/Projets"),
    ("Bash", "pytest -q"),
])
def test_commande_autorisee_sans_question(outil, commande):
    assert decision(lancer(outil, {"command": commande})) is None


@pytest.mark.parametrize("outil, commande", [
    ("Bash", 'cat "/d/Europa/recherche appartement.md"'),
    ("Bash", "ls /mnt/d/Europa/"),
    ("PowerShell", r"Get-ChildItem D:\Europa"),
    ("PowerShell", r'Get-Content "D:\Europa\5. Memoire IA\_INDEX.md"; Get-Content D:\Europa\x.md'),
    ("Bash", "cd D:/Europa && grep -r motif ."),
])
def test_commande_vers_le_coffre_perso_demande_confirmation(outil, commande):
    assert decision(lancer(outil, {"command": commande})) == "ask"


def test_commande_lancee_depuis_le_coffre_perso_demande_confirmation():
    assert decision(lancer("Bash", {"command": "cat note.md"}, cwd=r"D:\Europa\1.Projet")) == "ask"


def test_commande_qui_remonte_depuis_la_memoire_demande_confirmation():
    assert decision(lancer("Bash", {"command": "cat ../1.Projet/note.md"}, cwd=MEMOIRE)) == "ask"
    assert decision(lancer("Bash", {"command": "cat _INDEX.md"}, cwd=MEMOIRE)) is None


def test_outil_non_concerne_passe():
    assert decision(lancer("WebFetch", {"url": "https://example.com/Europa"})) is None


def test_entree_avec_bom_est_lue():
    # PowerShell ajoute un BOM quand il passe du texte à un programme : le hook doit quand même décider.
    entree = {"cwd": "D:\\", "tool_name": "Read", "tool_input": {"file_path": r"D:\Europa\x.md"}}
    resultat = subprocess.run([NODE, str(HOOK)], input="\ufeff" + json.dumps(entree), capture_output=True, text=True, encoding="utf-8")
    assert decision(resultat) == "ask"


def test_entree_illisible_ne_bloque_pas_mais_le_signale():
    resultat = subprocess.run([NODE, str(HOOK)], input="pas du json", capture_output=True, text=True, encoding="utf-8")
    assert resultat.returncode == 1
    assert resultat.stdout == ""
    assert "garde-europa" in resultat.stderr

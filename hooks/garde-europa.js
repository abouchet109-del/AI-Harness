// Hook PreToolUse de Claude Code : demande confirmation au user avant tout accès
// au coffre Obsidian perso (D:\Europa) en dehors de la mémoire IA (5. Memoire IA).
//
// Pourquoi un hook et pas une règle de permission : un refus l'emporte toujours
// sur une autorisation, on ne peut donc pas écrire « refuser D:\Europa sauf
// 5. Memoire IA » avec des règles. Pourquoi « ask » et pas « deny » : le user doit
// pouvoir autoriser un accès voulu à ses notes.
//
// Limite connue : pour les commandes shell, on lit le texte de la commande. Un
// chemin construit dans une variable passe inaperçu. C'est une protection contre
// les accès par erreur ou par injection évidente, pas une frontière de sécurité.
//
// Entrée : le JSON de PreToolUse sur stdin. Sortie : rien (le flux normal continue)
// ou une décision "ask". Entrée illisible : code 1, l'appel n'est pas bloqué.

const path = require("path");

const COFFRE = "d:\\europa";
const MEMOIRE = "d:\\europa\\5. memoire ia";
const RAISON =
  "Accès au coffre Obsidian perso (D:\\Europa hors « 5. Memoire IA »). " +
  "Les agents n'y vont que sur demande explicite du user.";

function versWindows(chemin) {
  let c = chemin.replace(/\//g, "\\");
  c = c.replace(/^\\\\([a-z]):\\/i, "$1:\\"); // //d:/...
  c = c.replace(/^\\mnt\\([a-z])\\/i, "$1:\\"); // /mnt/d/... (WSL)
  c = c.replace(/^\\([a-z])\\/i, "$1:\\"); // /d/... (Git Bash)
  return c;
}

function resoudre(cwd, chemin) {
  return path.win32.resolve(versWindows(cwd || "."), versWindows(chemin || ".")).toLowerCase();
}

function dedans(chemin, dossier) {
  return chemin === dossier || chemin.startsWith(dossier + "\\");
}

// "memoire", "perso", "ancetre" (contient le coffre, comme D:\) ou "dehors".
function classer(chemin) {
  if (dedans(chemin, MEMOIRE)) return "memoire";
  if (dedans(chemin, COFFRE)) return "perso";
  if (dedans(COFFRE, chemin.replace(/\\$/, ""))) return "ancetre";
  return "dehors";
}

function prefixeDuMotif(motif) {
  const debutGlob = motif.search(/[*?[{]/);
  const fixe = debutGlob === -1 ? motif : motif.slice(0, debutGlob);
  const coupure = Math.max(fixe.lastIndexOf("/"), fixe.lastIndexOf("\\"));
  return coupure === -1 ? "" : fixe.slice(0, coupure + 1);
}

function fichierSensible(entree) {
  const outil = entree.tool_name;
  const params = entree.tool_input || {};
  if (["Read", "Write", "Edit"].includes(outil)) {
    return params.file_path && classer(resoudre(entree.cwd, params.file_path)) === "perso";
  }
  if (outil === "NotebookEdit") {
    return params.notebook_path && classer(resoudre(entree.cwd, params.notebook_path)) === "perso";
  }
  if (outil === "Grep" || outil === "Glob") {
    const base = resoudre(entree.cwd, params.path);
    const cibles = [base];
    if (outil === "Glob" && params.pattern) cibles.push(resoudre(base, prefixeDuMotif(params.pattern)));
    return cibles.some((c) => ["perso", "ancetre"].includes(classer(c)));
  }
  return false;
}

function commandeSensible(entree) {
  const outil = entree.tool_name;
  if (outil !== "Bash" && outil !== "PowerShell") return false;
  const lieu = classer(resoudre(entree.cwd, "."));
  const commande = String((entree.tool_input || {}).command || "")
    .toLowerCase()
    .replace(/\//g, "\\")
    .replace(/\\ /g, " ")
    .replace(/`/g, "");
  if (lieu === "perso") return true;
  if (lieu === "memoire" && commande.includes("..")) return true;

  const mention = /(^|[\\\s:"'=(])europa(?=$|[\\\s"';|&)])/g;
  let trouve;
  while ((trouve = mention.exec(commande)) !== null) {
    const suite = commande.slice(trouve.index + trouve[1].length);
    const versMemoire = suite.match(/^europa\\5\. memoire ia(?=$|[\\\s"';|&)])([^"'\s;|&)]*)/);
    if (!versMemoire || versMemoire[1].includes("..")) return true;
  }
  return false;
}

function decider(entree) {
  if (!fichierSensible(entree) && !commandeSensible(entree)) return null;
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: RAISON,
    },
  };
}

let brut = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (morceau) => (brut += morceau));
process.stdin.on("end", () => {
  let entree;
  try {
    entree = JSON.parse(brut.replace(/^﻿/, ""));
  } catch (erreur) {
    process.stderr.write(`garde-europa : entrée illisible, appel non vérifié (${erreur.message})\n`);
    process.exit(1);
  }
  const sortie = decider(entree);
  if (sortie) process.stdout.write(JSON.stringify(sortie));
  process.exit(0);
});

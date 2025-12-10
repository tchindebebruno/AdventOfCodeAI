
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import anthropic
import subprocess
import os
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

# =========================
# 1. Modèles & Scraping
# =========================
CLAUDE_MODEL = "claude-sonnet-4-20250514"
GPT_MODEL = "o3-mini"
GEMINI_MODEL = "gemini-2.5-flash"

# Config Gemini (utilise GOOGLE_API_KEY)
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
gemini_model = genai.GenerativeModel(GEMINI_MODEL)


def remove_code_fences(text: str) -> str:
    lines = text.strip().splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Ignore lines that are code fences like ``` or ```python
        if stripped.startswith("```"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def scrape_text(url: str, selector: str | None = None) -> str:
    """
    Scrape le texte d'une page web.
    - url : URL de la page à scraper
    - selector : sélecteur CSS pour cibler une zone précise (optionnel)
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    if not selector:
        return soup.get_text(separator="\n", strip=True)

    elements = soup.select(selector)
    return "\n\n".join([el.get_text(strip=True) for el in elements])


# =========================
# 2. Lecture fichier input / énoncé
# =========================

def read_text_file(path: str, encoding: str = "utf-8") -> str | None:
    """
    Lit et renvoie le contenu d'un fichier texte.
    """
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        print(f"Erreur : fichier introuvable → {path}")
    except UnicodeDecodeError:
        print("Erreur : problème d'encodage. Essayez encoding='latin-1'")
    except Exception as e:
        print(f"Erreur inconnue : {e}")
    return None


# =========================
# 3. Clients LLM
# =========================

openai_client = OpenAI()                 # utilise OPENAI_API_KEY
claude_client = anthropic.Anthropic()    # utilise ANTHROPIC_API_KEY

# 🔁 Nouvelle consigne : lire 'input.txt' dans le même répertoire que le script généré
COMMON_INSTRUCTION_PART2 = r"""
You are an expert in Advent of Code, text parsing, and algorithms.

The problem consists of two parts.
Part 1 defines the base rules.
Part 2 modifies or extends those rules.

You MAY use Pulp, SciPy linprog, or any other suitable library.

TASK:

Write a COMPLETE Python 3 script.

INPUT SOURCE (MANDATORY):
The script MUST READ the input from a local file named `input.txt` located in the SAME DIRECTORY as the generated script.
Do NOT read from stdin.
Example pattern (not mandatory): open('input.txt', 'r', encoding='utf-8').read()

PARSING:
Parse the input exactly as described by the problem.

TARGET:
Compute the correct answer for PART 2 ONLY, applying Part 1 rules as modified/extended by Part 2.

OUTPUT:
PRINT ONLY the final answer (a single line or value).
No explanatory text, no comments, no debug logs.

OUTPUT CONSTRAINTS (CRITICAL):
Do NOT include any markdown code fences or backticks.
Do NOT include explanations or surrounding text.
The response must be ONLY raw executable Python code.

SUMMARY:
Output = a single fully executable Python 3 script that reads from `input.txt` in the same directory, prints ONLY the final answer, with zero markdown/prose/extraneous characters.
"""


# =========================
# 3.a Génération de code PARTIE 2 avec ChatGPT (OpenAI)
# =========================

def generate_solver_code_gpt_part2(problem_part1_text: str, problem_part2_text: str) -> str:
    prompt = f"""
Here is PART 1 (context):
-----------------------------------------
{problem_part1_text}

Here is PART 2 (to implement):
-----------------------------------------
{problem_part2_text}
"""
    response = openai_client.responses.create(
        model=GPT_MODEL,  # ou "gpt-5.1" si tu l'as
        input=[
            {"role": "system", "content": COMMON_INSTRUCTION_PART2},
            {"role": "user", "content": prompt}
        ],
    )
    code = getattr(response, "output_text", None)
    if not code:
        # Fallback extraction if SDK variant returns structured content
        parts = []
        for item in getattr(response, "output", []):
            if getattr(item, "type", "") == "message":
                for content_part in item.message.content:
                    if getattr(content_part, "type", "") == "text":
                        parts.append(content_part.text)
        code = "\n".join(parts)
    return code


# =========================
# 3.b Génération de code PARTIE 2 avec Claude (Anthropic)
# =========================

def generate_solver_code_claude_part2(problem_part1_text: str, problem_part2_text: str) -> str:
    prompt = f"""
Here is PART 1 (context):
-----------------------------------------
{problem_part1_text}

Here is PART 2 (to implement):
-----------------------------------------
{problem_part2_text}
"""
    resp = claude_client.messages.create(
        model=CLAUDE_MODEL,
        # max_tokens=8192,
        system=COMMON_INSTRUCTION_PART2,   # ✅ top-level
        messages=[
            {"role": "system", "content": COMMON_INSTRUCTION_PART2},
            {"role": "user", "content": prompt}
        ],
    )

    parts = []
    for block in resp.content:
        if block.type == "text":
            parts.append(block.text)
    code = "".join(parts)
    return code


# =========================
# 3.c Génération de code PARTIE 2 avec Gemini
# =========================

def generate_solver_code_gemini_part2(problem_part1_text: str, problem_part2_text: str) -> str:
    prompt = f"""
{COMMON_INSTRUCTION_PART2}
Here is PART 1 (context):
-----------------------------------------
{problem_part1_text}

Here is PART 2 (to implement):
-----------------------------------------
{problem_part2_text}
"""
    try:
        resp = gemini_model.generate_content(prompt)
        code = resp.text or ""
        code = remove_code_fences(code)
        return code
    except GoogleAPIError as e:
        print("⚠️ Gemini PARTIE 2 : erreur API (quota, modèle, etc.). On ignore Gemini pour cette exécution.")
        print(e)
        return ""
    except Exception as e:
        print("⚠️ Gemini PARTIE 2 : erreur inattendue. On ignore Gemini.")
        print(e)
        return ""


# =========================
# 4. Sauvegarde du code généré
# =========================

def save_code_to_file(code: str, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)


# =========================
# 5. Exécution du code généré (lit input.txt dans son répertoire)
# =========================

def execute_generated_code(filename: str) -> str:
    """
    Exécute le script Python généré. Le script généré lit lui-même 'input.txt'
    dans son répertoire (selon la consigne). On ne lui passe pas stdin.
    Retourne la sortie (stdout).
    """
    # S'assure que le cwd contient le script et potentiellement input.txt
    cwd = os.path.dirname(os.path.abspath(filename)) or os.getcwd()

    process = subprocess.Popen(
        ["python", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd
    )

    stdout, stderr = process.communicate()

    if stderr:
        print(f"⚠️ Erreur dans le code généré ({filename}) :", stderr)

    return (stdout or "").strip()


# =========================
# 6. Pipeline complet AoC PARTIE 2 (GPT + Claude + Gemini)
# =========================

def solve_advent_of_code_part2_with_all(problem_url: str, input_path: str, part2_path: str):
    """
    - Scrap l’énoncé AoC (partie 1)
    - Lit l’énoncé spécifique de la partie 2 depuis un fichier (enonce2.txt)
    - (Le script généré lira 'input.txt' lui-même dans son répertoire)
    - Demande à GPT, Claude et Gemini de générer un solver Python pour la PARTIE 2
    - Sauvegarde les trois solvers
    - Exécute les trois solvers (sans stdin)
    - Affiche les trois réponses
    """
    selector = "article.day-desc"

    print("Scraping de l'énoncé (partie 1) sur :", problem_url)
    problem_part1_text = scrape_text(problem_url, selector)

    print("Lecture de l'énoncé PARTIE 2 depuis :", part2_path)
    problem_part2_text = read_text_file(part2_path) or ""

    # Optionnel : lecture locale de l'input pour validation humaine
    # (le script généré ne lira pas cette variable, c'est pour debug)
    print("Lecture de l'input depuis :", input_path)
    input_text_debug = read_text_file(input_path)
    if input_text_debug is None:
        print("⚠️ Attention : 'input.txt' introuvable. Placez-le dans le même répertoire que ce programme et les scripts générés.")

    # ========= ChatGPT =========
    result_gpt = None
    try:
        print("\n=== [ChatGPT] Génération du code solveur PARTIE 2... ===\n")
        code_gpt = generate_solver_code_gpt_part2(problem_part1_text, problem_part2_text)
        filename_gpt = "generated_solution_part2_gpt.py"
        save_code_to_file(code_gpt, filename_gpt)
        print(f"[ChatGPT] Code généré et sauvegardé dans {filename_gpt}\n")

        print("[ChatGPT] Exécution du solveur (lit input.txt dans le même répertoire)...\n")
        result_gpt = execute_generated_code(filename_gpt)
        print(f"[ChatGPT] Réponse : {result_gpt}\n")
    except Exception as e:
        print(f"❌ Erreur pipeline ChatGPT PARTIE 2 : {e}")

    # ========= Claude =========
    result_claude = None
    try:
        print("\n=== [Claude] Génération du code solveur PARTIE 2... ===\n")
        code_claude = generate_solver_code_claude_part2(problem_part1_text, problem_part2_text)
        filename_claude = "generated_solution_part2_claude.py"
        save_code_to_file(code_claude, filename_claude)
        print(f"[Claude] Code généré et sauvegardé dans {filename_claude}\n")

        print("[Claude] Exécution du solveur (lit input.txt dans le même répertoire)...\n")
        result_claude = execute_generated_code(filename_claude)
        print(f"[Claude] Réponse : {result_claude}\n")
    except Exception as e:
        print(f"❌ Erreur pipeline Claude PARTIE 2 : {e}")

    # ========= Gemini =========
    result_gemini = None
    try:
        print("\n=== [Gemini] Génération du code solveur PARTIE 2... ===\n")
        code_gemini = generate_solver_code_gemini_part2(problem_part1_text, problem_part2_text)

        if code_gemini.strip():
            filename_gemini = "generated_solution_part2_gemini.py"
            save_code_to_file(code_gemini, filename_gemini)
            print(f"[Gemini] Code généré et sauvegardé dans {filename_gemini}\n")

            print("[Gemini] Exécution du solveur (lit input.txt dans le même répertoire)...\n")
            result_gemini = execute_generated_code(filename_gemini)
            print(f"[Gemini] Réponse : {result_gemini}\n")
        else:
            print("[Gemini] Aucun code généré (quota / modèle / erreur). On saute l'exécution.\n")
    except Exception as e:
        print(f"❌ Erreur pipeline Gemini PARTIE 2 : {e}")

    # ========= Récap =========
    print("\n===== RÉPONSES FINALES PARTIE 2 =====")
    print(f"ChatGPT : {result_gpt}")
    print(f"Claude  : {result_claude}")
    print(f"Gemini  : {result_gemini}")
    print("=====================================")

    return result_gpt, result_claude, result_gemini


# =========================
# 7. Main
# =========================

if __name__ == "__main__":
    url = "https://adventofcode.com/2025/day/10"
    input_file = "input.txt"
    part2_file = "enonce2.txt"   # fichier où tu as collé l'énoncé de la partie 2

    solve_advent_of_code_part2_with_all(url, input_file, part2_file)

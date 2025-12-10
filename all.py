import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import anthropic
import subprocess
import google.generativeai as genai
from playwright.sync_api import sync_playwright
import os

# =========================
# 0. Modèles & config
# =========================

# CLAUDE_MODEL = "claude-haiku-4-5"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
GPT_MODEL = "o3"
# GEMINI_MODEL = "gemini-2.5-pro"
GEMINI_MODEL = "gemini-2.5-flash"

# Config Gemini (nécessite GEMINI_API_KEY dans les variables d'env)
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))


# =========================
# 1. Scraping
# =========================

def fetch_and_save_to_file(url: str, selector: str, output_file: str = "input.txt") -> None:
    """
    Ouvre une page avec la session edge_state.json,
    récupère le texte du selecteur CSS donné
    et l'ajoute à output_file.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="edge_state.json")

        page = context.new_page()

        # On récupère la réponse principale
        response = page.goto(url)

        # Petit délai si la page charge du JS
        page.wait_for_timeout(2000)

        if not response:
            print("❓ Impossible d'obtenir la réponse principale")
        else:
            print("✅ Statut HTTP :", response.status)

        print("🌐 URL finale :", page.url)

        # Récupération du contenu via le sélecteur
        if selector:
            locator = page.locator(selector)
            count = locator.count()
            if count == 0:
                print(f"⚠️ Aucun élément trouvé pour le sélecteur : {selector}")
                content = ""
            else:
                # On concatène tous les innerText trouvés
                texts = locator.all_inner_texts()
                content = "\n".join(t.strip() for t in texts if t.strip())
        else:
            # Si pas de sélecteur, on prend tout le texte de la page
            content = page.inner_text("body")

        # On écrit dans le fichier en mode append
        if content:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"💾 Contenu ajouté à {output_file}")
        else:
            print("⚠️ Aucun contenu à écrire dans le fichier.")

        browser.close()

def scrape_text(url, selector=None):
    """
    Scrape le texte d'une page web.
    - url : URL de la page à scraper
    - selector : sélecteur CSS pour cibler une zone précise (optionnel)
    """

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Si aucun sélecteur → on récupère tout le texte
    if not selector:
        return soup.get_text(separator="\n", strip=True)

    # Avec sélecteur CSS
    elements = soup.select(selector)
    
    return "\n".join([el.get_text(strip=True) for el in elements])


# =========================
# 2. Lecture fichier input
# =========================

def read_text_file(path, encoding="utf-8"):
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


# =========================
# 3. Clients LLM
# =========================

openai_client = OpenAI()                # utilise OPENAI_API_KEY
claude_client = anthropic.Anthropic()   # utilise ANTHROPIC_API_KEY
gemini_model = genai.GenerativeModel(GEMINI_MODEL)  # utilise GEMINI_API_KEY


COMMON_INSTRUCTION = """
You are an expert in Advent of Code, text parsing, and algorithms.

TASK:
- Write a COMPLETE Python 3 script.
- The script must READ the input from stdin (e.g., using sys.stdin.read()).
- It must PARSE the input exactly as described in the problem.
- It must COMPUTE the required answer for PART 1.
- It must PRINT ONLY the final answer.
- No extra output of any kind is allowed.

OUTPUT CONSTRAINTS (VERY IMPORTANT):
- Your response must contain ONLY raw Python code, directly executable.
- Do NOT include any markdown code fences: no ``` and no ```python, and no backticks at all.
- Do NOT include any explanations, comments, logging, or prose.
- Absolutely no text outside the Python code.

SUMMARY:
- Response = only a full Python 3 script, with zero markdown, zero backticks, and zero surrounding text.
"""

def remove_code_fences(text):
    lines = text.strip().splitlines()

    cleaned = []
    for line in lines:
        stripped = line.strip()

        # Ignore lines that are code fences like ``` or ```python or ```anything
        if stripped.startswith("```"):
            continue

        cleaned.append(line)

    return "\n".join(cleaned)
# =========================
# 3.a Génération de code avec ChatGPT (OpenAI)
# =========================

def generate_solver_code_chatgpt(problem_statement: str) -> str:
    """
    Demande à ChatGPT (OpenAI) de générer un script Python solveur.
    """

    prompt = f"""
{COMMON_INSTRUCTION}

Voici l'énoncé du problème (incluant éventuellement des exemples) :

{problem_statement}
"""

    response = openai_client.responses.create(
        model=GPT_MODEL,
        input=[{"role": "user", "content": prompt}],
    )

    code = response.output_text
    return code


# =========================
# 3.b Génération de code avec Claude (Anthropic)
# =========================

def generate_solver_code_claude(problem_statement: str) -> str:
    """
    Demande à Claude de générer un script Python solveur.
    """

    prompt = f"""
{COMMON_INSTRUCTION}

Voici l'énoncé du problème (incluant éventuellement des exemples) :

{problem_statement}
"""

    resp = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    parts = []
    for block in resp.content:
        if block.type == "text":
            parts.append(block.text)
    code = "".join(parts)
    return code


# =========================
# 3.c Génération de code avec Gemini
# =========================

def generate_solver_code_gemini(problem_statement: str) -> str:
    """
    Demande à Gemini de générer un script Python solveur.
    """

    prompt = f"""
{COMMON_INSTRUCTION}

Voici l'énoncé du problème (incluant éventuellement des exemples) :

{problem_statement}
"""

    resp = gemini_model.generate_content(prompt)

    # Sur le client google.generativeai, le texte principal est en resp.text
    code = resp.text or ""
    code = remove_code_fences(code)
    return code


# =========================
# 4. Sauvegarde du code généré
# =========================

def save_code_to_file(code: str, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)


# =========================
# 5. Exécution du code généré sur l'input AoC
# =========================

def execute_generated_code(input_text: str, filename: str) -> str:
    """
    Exécute le script Python généré en lui passant input_text sur stdin.
    Retourne la sortie (stdout) du script.
    """
    process = subprocess.Popen(
        ["python", filename],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate(input_text)

    if stderr:
        print(f"⚠️ Erreur dans le code généré ({filename}) :", stderr)

    return stdout.strip()


# =========================
# 6. Pipeline complet AoC (Partie 1, duel/truel Claude vs ChatGPT vs Gemini)
# =========================

def solve_advent_of_code_with_all(problem_url: str, input_path: str):
    """
    - Scrap l'énoncé AoC
    - Lit l'input local
    - Demande à Claude, ChatGPT et Gemini de générer chacun un solver Python
    - Sauvegarde les trois solvers
    - Exécute les trois solvers sur le même input
    - Affiche les trois réponses
    """
    selector = "article.day-desc"

    print("Scraping de l'énoncé sur :", problem_url)
    problem_text = scrape_text(problem_url, selector)

    print("Lecture de l'input depuis :", input_path)
    input_text = read_text_file(input_path)

    # ---- ChatGPT ----
    print("\nGénération du code solveur PARTIE 1 avec ChatGPT...\n")
    code_chatgpt = generate_solver_code_chatgpt(problem_text)
    filename_chatgpt = "solution_chatgpt.py"
    save_code_to_file(code_chatgpt, filename_chatgpt)
    print(f"Code ChatGPT généré et sauvegardé dans {filename_chatgpt}\n")

    print("Exécution du solveur ChatGPT sur l'input...\n")
    result_chatgpt = execute_generated_code(input_text, filename_chatgpt)
    print("Résultat ChatGPT :", result_chatgpt)

    # ---- Claude ----
    print("\nGénération du code solveur PARTIE 1 avec Claude...\n")
    code_claude = generate_solver_code_claude(problem_text)
    filename_claude = "solution_claude.py"
    save_code_to_file(code_claude, filename_claude)
    print(f"Code Claude généré et sauvegardé dans {filename_claude}\n")

    print("Exécution du solveur Claude sur l'input...\n")
    result_claude = execute_generated_code(input_text, filename_claude)
    print("Résultat Claude :", result_claude)

   

    # ---- Gemini ----
    print("\nGénération du code solveur PARTIE 1 avec Gemini...\n")
    code_gemini = generate_solver_code_gemini(problem_text)
    filename_gemini = "solution_gemini.py"
    save_code_to_file(code_gemini, filename_gemini)
    print(f"Code Gemini généré et sauvegardé dans {filename_gemini}\n")

    print("Exécution du solveur Gemini sur l'input...\n")
    result_gemini = execute_generated_code(input_text, filename_gemini)
    print("Résultat Gemini :", result_gemini)

    # ---- Résumé ----
    print("\n===== RÉPONSES FINALES PARTIE 1 =====")
    print(f"ChatGPT : {result_chatgpt}")
    print(f"Claude  : {result_claude}")
    print(f"Gemini  : {result_gemini}")
    print("=====================================")

    return result_chatgpt, result_claude, result_gemini


# =========================
# 7. Main
# =========================

if __name__ == "__main__":
    url = "https://adventofcode.com/2025/day/5"
    input_file = "input.txt"
    rep = input("Appuie sur Entrée pour continuer: ")
    print("Obtention de l'input et résolution du problème...")
    # fetch_and_save_to_file(
    #     f"{url}/input",
    #     selector="pre",
    #     output_file=input_file
    # )
    solve_advent_of_code_with_all(url, input_file)

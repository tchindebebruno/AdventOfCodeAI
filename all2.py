import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import anthropic
import subprocess

# =========================
# 1. Scraping
# =========================

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
# 2. Lecture fichier input / énoncé
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

openai_client = OpenAI()                 # utilise OPENAI_API_KEY
claude_client = anthropic.Anthropic()    # utilise ANTHROPIC_API_KEY

COMMON_INSTRUCTION_PART2 = """
Tu es un expert en Advent of Code, parsing de texte et algorithmique.

Le problème se compose de deux parties.
La partie 1 définit les règles de base, la partie 2 les modifie / complète.

TÂCHE :
- Écris un script Python 3 COMPLET.
- Le script doit LIRE l'input depuis stdin (par exemple via sys.stdin.read()).
- Il doit PARSER l'input tel que décrit dans le problème.
- Il doit CALCULER la réponse attendue pour la PARTIE 2 uniquement,
  en tenant compte des règles de la partie 1 modifiées/complétées par la partie 2.
- Il doit AFFICHER UNIQUEMENT la réponse finale avec un print.
- Pas de texte explicatif, pas de commentaires, pas de logging superflu.

IMPORTANT :
- Ne mets PAS de ``` autour du code.
- Ne mets PAS d'explications autour. Seulement du code Python exécutable.
"""


# =========================
# 3.a Génération de code PARTIE 2 avec ChatGPT (OpenAI)
# =========================

def generate_solver_code_gpt_part2(problem_part1_text: str, problem_part2_text: str) -> str:
    prompt = f"""
{COMMON_INSTRUCTION_PART2}

Voici l'énoncé de la PARTIE 1 (contexte) :
-----------------------------------------
{problem_part1_text}

Voici l'énoncé de la PARTIE 2 (celle que tu dois implémenter) :
----------------------------------------------------------------
{problem_part2_text}
"""

    response = openai_client.responses.create(
        model="gpt-4.1",  # ou "gpt-5.1" si tu l'as
        input=[{"role": "user", "content": prompt}],
    )

    code = response.output_text
    return code


# =========================
# 3.b Génération de code PARTIE 2 avec Claude (Anthropic)
# =========================

CLAUDE_MODEL = "claude-sonnet-4-20250514"  # adapte si besoin selon ton compte

def generate_solver_code_claude_part2(problem_part1_text: str, problem_part2_text: str) -> str:
    prompt = f"""
{COMMON_INSTRUCTION_PART2}

Voici l'énoncé de la PARTIE 1 (contexte) :
-----------------------------------------
{problem_part1_text}

Voici l'énoncé de la PARTIE 2 (celle que tu dois implémenter) :
----------------------------------------------------------------
{problem_part2_text}
"""

    resp = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
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
# 6. Pipeline complet AoC PARTIE 2 (GPT + Claude)
# =========================

def solve_advent_of_code_part2_with_both(problem_url: str, input_path: str, part2_path: str):
    """
    - Scrap l’énoncé AoC (partie 1)
    - Lit l’énoncé spécifique de la partie 2 depuis un fichier (enonce2.txt)
    - Lit l’input local
    - Demande à GPT de générer un solver Python pour la PARTIE 2
    - Demande à Claude de générer un solver Python pour la PARTIE 2
    - Sauvegarde les deux solvers
    - Exécute les deux solvers sur l’input
    - Affiche les deux réponses
    """
    selector = "article.day-desc"

    print("Scraping de l'énoncé (partie 1) sur :", problem_url)
    problem_part1_text = scrape_text(problem_url, selector)

    print("Lecture de l'énoncé PARTIE 2 depuis :", part2_path)
    problem_part2_text = read_text_file(part2_path)

    print("Lecture de l'input depuis :", input_path)
    input_text = read_text_file(input_path)

    # ========= Claude =========
    result_claude = None
    try:
        print("\n=== [Claude] Génération du code solveur PARTIE 2... ===\n")
        code_claude = generate_solver_code_claude_part2(problem_part1_text, problem_part2_text)
        filename_claude = "generated_solution_part2_claude.py"
        save_code_to_file(code_claude, filename_claude)
        print(f"[Claude] Code généré et sauvegardé dans {filename_claude}\n")

        print("[Claude] Exécution du solveur sur l'input...\n")
        result_claude = execute_generated_code(input_text, filename_claude)
        print(f"[Claude] Réponse : {result_claude}\n")
    except Exception as e:
        print(f"❌ Erreur pipeline Claude PARTIE 2 : {e}")

    # ========= ChatGPT =========
    result_gpt = None
    try:
        print("\n=== [ChatGPT] Génération du code solveur PARTIE 2... ===\n")
        code_gpt = generate_solver_code_gpt_part2(problem_part1_text, problem_part2_text)
        filename_gpt = "generated_solution_part2_gpt.py"
        save_code_to_file(code_gpt, filename_gpt)
        print(f"[ChatGPT] Code généré et sauvegardé dans {filename_gpt}\n")

        print("[ChatGPT] Exécution du solveur sur l'input...\n")
        result_gpt = execute_generated_code(input_text, filename_gpt)
        print(f"[ChatGPT] Réponse : {result_gpt}\n")
    except Exception as e:
        print(f"❌ Erreur pipeline ChatGPT PARTIE 2 : {e}")

    # ========= Récap =========
    print("\n===== RÉPONSES FINALES PARTIE 2 =====")
    print(f"ChatGPT : {result_gpt}")
    print(f"Claude  : {result_claude}")
    print("=====================================")

    return result_gpt, result_claude


# =========================
# 7. Main
# =========================

if __name__ == "__main__":
    url = "https://adventofcode.com/2025/day/3"
    input_file = "input.txt"
    part2_file = "enonce2.txt"   # fichier où tu as collé l'énoncé de la partie 2

    solve_advent_of_code_part2_with_both(url, input_file, part2_file)

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

openai_client = OpenAI()           # utilise OPENAI_API_KEY
claude_client = anthropic.Anthropic()  # utilise ANTHROPIC_API_KEY


COMMON_INSTRUCTION = """
Tu es un expert en Advent of Code, parsing de texte et algorithmique.

TÂCHE :
- Écris un script Python 3 COMPLET.
- Le script doit LIRE l'input depuis stdin (par exemple via sys.stdin.read()).
- Il doit PARSER l'input tel que décrit dans le problème.
- Il doit CALCULER la réponse attendue pour la PARTIE 1.
- Il doit AFFICHER UNIQUEMENT la réponse finale avec un print.
- Pas de texte explicatif, pas de commentaires, pas de logging superflu.

IMPORTANT :
- Ne mets PAS de ``` autour du code.
- Ne mets PAS d'explications autour. Seulement du code Python exécutable.
"""


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
        model="gpt-4.1",  # ou "gpt-5.1" selon ton compte
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
        model="claude-sonnet-4-20250514",  # adapte si besoin
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    # Anthropic renvoie une liste de blocks ; on concatène les blocs de type "text"
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
# 6. Pipeline complet AoC (Partie 1, duel ChatGPT vs Claude)
# =========================

def solve_advent_of_code_with_both(problem_url: str, input_path: str):
    """
    - Scrap l'énoncé AoC
    - Lit l'input local
    - Demande à ChatGPT de générer un solver Python
    - Demande à Claude de générer un solver Python
    - Sauvegarde les deux solvers
    - Exécute les deux solvers sur le même input
    - Affiche les deux réponses
    """
    selector = "article.day-desc"

    print("Scraping de l'énoncé sur :", problem_url)
    problem_text = scrape_text(problem_url, selector)

    print("Lecture de l'input depuis :", input_path)
    input_text = read_text_file(input_path)

    # ---- Claude ----
    print("\nGénération du code solveur PARTIE 1 avec Claude...\n")
    code_claude = generate_solver_code_claude(problem_text)
    filename_claude = "solution_claude.py"
    save_code_to_file(code_claude, filename_claude)
    print(f"Code Claude généré et sauvegardé dans {filename_claude}\n")

    print("Exécution du solveur Claude sur l'input...\n")
    result_claude = execute_generated_code(input_text, filename_claude)
    print("Résultat Claude :", result_claude)

    # ---- ChatGPT ----
    print("\nGénération du code solveur PARTIE 1 avec ChatGPT...\n")
    code_chatgpt = generate_solver_code_chatgpt(problem_text)
    filename_chatgpt = "solution_chatgpt.py"
    save_code_to_file(code_chatgpt, filename_chatgpt)
    print(f"Code ChatGPT généré et sauvegardé dans {filename_chatgpt}\n")

    print("Exécution du solveur ChatGPT sur l'input...\n")
    result_chatgpt = execute_generated_code(input_text, filename_chatgpt)
    print("Résultat ChatGPT :", result_chatgpt)

    # ---- Résumé ----
    print("\n===== RÉPONSES FINALES PARTIE 1 =====")
    print(f"ChatGPT : {result_chatgpt}")
    print(f"Claude  : {result_claude}")
    print("=====================================")

    return result_chatgpt, result_claude


# =========================
# 7. Main
# =========================

if __name__ == "__main__":
    url = "https://adventofcode.com/2025/day/3"
    input_file = "input.txt"

    solve_advent_of_code_with_both(url, input_file)

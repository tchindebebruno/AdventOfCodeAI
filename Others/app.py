import requests
from bs4 import BeautifulSoup
from openai import OpenAI
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
    
    paramètres :
        path (str) : chemin vers le fichier .txt
        encoding (str) : encodage du fichier (par défaut UTF-8)
    
    renvoie :
        str : contenu complet du fichier
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
# 3. Génération de code avec GPT
# =========================

client = OpenAI()  # utilise OPENAI_API_KEY

def generate_solver_code(problem_statement: str) -> str:
    """
    Demande au modèle de générer un script Python qui :
    - lit l'input depuis stdin
    - calcule la réponse
    - affiche UNIQUEMENT la réponse finale (print)
    """

    prompt = f"""
Tu es un expert en Advent of Code, parsing de texte et algorithmique.

TÂCHE :
- Écris un script Python 3 COMPLET.
- Le script doit LIRE l'input depuis stdin (sys.stdin.read() par exemple).
- Il doit PARSER l'input tel que décrit dans le problème.
- Il doit CALCULER la réponse attendue (partie indiquée dans l'énoncé).
- Il doit AFFICHER UNIQUEMENT la réponse finale avec un print.
- Pas de texte explicatif, pas de commentaires, pas de logging superflu.

IMPORTANT :
- Ne mets PAS de ``` autour du code.
- Ne mets PAS d'explications autour. Seulement du code Python exécutable.

Voici l'énoncé du problème (incluant éventuellement des exemples) :

{problem_statement}
"""

    response = client.responses.create(
        model="gpt-4.1",  # ou "o3" si tu l'as
        input=[{"role": "user", "content": prompt}],
    )

    # Sur les nouveaux SDK, output_text contient tout le texte de sortie
    code = response.output_text
    return code


# =========================
# 4. Sauvegarde du code généré
# =========================

def save_code_to_file(code: str, filename: str = "generated_solution.py"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)


# =========================
# 5. Exécution du code généré sur l'input AoC
# =========================

def execute_generated_code(input_text: str, filename: str = "generated_solution.py") -> str:
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
        print("⚠️ Erreur dans le code généré :", stderr)

    return stdout.strip()


# =========================
# 6. Pipeline complet AoC
# =========================

def solve_advent_of_code_via_generated_code(problem_url: str, input_path: str):
    """
    - Scrap l'énoncé AoC
    - Lit l'input local
    - Demande à GPT de générer un solver Python
    - Sauvegarde le solver
    - Exécute le solver sur l'input
    - Affiche la réponse finale
    """
    selector = "article.day-desc"

    print("Scraping de l'énoncé sur :", problem_url)
    problem_text = scrape_text(problem_url, selector)

    print("Lecture de l'input depuis :", input_path)
    input_text = read_text_file(input_path)

    print("\nGénération du code solveur avec GPT...\n")
    code = generate_solver_code(problem_text)

    save_code_to_file(code)
    print("Code généré et sauvegardé dans generated_solution.py\n")

    print("Exécution du solveur sur l'input...\n")
    result = execute_generated_code(input_text)

    print("\n===== RÉPONSE FINALE =====")
    print(result)
    print("==========================")

    return result


# =========================
# 7. Main
# =========================

if __name__ == "__main__":
    url = "https://adventofcode.com/2025/day/1"
    input_file = "input.txt"

    solve_advent_of_code_via_generated_code(url, input_file)

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
# 3. Génération de code avec GPT
# =========================

client = OpenAI()  # utilise OPENAI_API_KEY

def generate_solver_code(problem_part1_text: str, problem_part2_text: str) -> str:
    """
    Demande au modèle de générer un script Python qui résout la PARTIE 2 :
    - lit l'input depuis stdin
    - calcule la réponse de la partie 2
    - affiche UNIQUEMENT la réponse finale (print)
    """

    prompt = f"""
Tu es un expert en Advent of Code, parsing de texte et algorithmique.

Le problème se compose de deux parties.
La partie 1 définit les règles de base, la partie 2 les modifie / complète.

Voici l'énoncé de la PARTIE 1 (contexte) :
-----------------------------------------
{problem_part1_text}

Voici l'énoncé de la PARTIE 2 (celle que tu dois implémenter) :
----------------------------------------------------------------
{problem_part2_text}

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

    response = client.responses.create(
        model="gpt-4.1",  # tu peux remplacer par "gpt-5.1" si dispo
        input=[{"role": "user", "content": prompt}],
    )

    code = response.output_text
    return code


# =========================
# 4. Sauvegarde du code généré
# =========================

def save_code_to_file(code: str, filename: str = "generated_solution_part2.py"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)


# =========================
# 5. Exécution du code généré sur l'input AoC
# =========================

def execute_generated_code(input_text: str, filename: str = "generated_solution_part2.py") -> str:
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
# 6. Pipeline complet AoC PARTIE 2
# =========================

def solve_advent_of_code_part2(problem_url: str, input_path: str, part2_path: str):
    """
    - Scrap l’énoncé AoC (partie 1 + éventuellement 2 si déjà visibles sur la page)
    - Lit l’énoncé spécifique de la partie 2 depuis un fichier (enonce2.txt)
    - Lit l’input local
    - Demande à GPT de générer un solver Python pour la PARTIE 2
    - Sauvegarde le solver
    - Exécute le solver sur l’input
    - Affiche la réponse finale
    """
    selector = "article.day-desc"

    print("Scraping de l'énoncé (partie 1) sur :", problem_url)
    problem_part1_text = scrape_text(problem_url, selector)

    print("Lecture de l'énoncé PARTIE 2 depuis :", part2_path)
    problem_part2_text = read_text_file(part2_path)

    print("Lecture de l'input depuis :", input_path)
    input_text = read_text_file(input_path)

    print("\nGénération du code solveur PARTIE 2 avec GPT...\n")
    code = generate_solver_code(problem_part1_text, problem_part2_text)

    save_code_to_file(code)
    print("Code généré et sauvegardé dans generated_solution_part2.py\n")

    print("Exécution du solveur sur l'input...\n")
    result = execute_generated_code(input_text)

    print("\n===== RÉPONSE FINALE PARTIE 2 =====")
    print(result)
    print("===================================")

    return result


# =========================
# 7. Main
# =========================

if __name__ == "__main__":
    url = "https://adventofcode.com/2025/day/1"
    input_file = "input.txt"
    part2_file = "enonce2.txt"   # fichier où tu as collé l'énoncé de la partie 2

    solve_advent_of_code_part2(url, input_file, part2_file)

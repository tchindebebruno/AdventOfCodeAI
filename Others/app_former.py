import requests
from bs4 import BeautifulSoup
from openai import OpenAI

def solve_advent_of_code_stream(problem_statement: str) -> str:
    """
    Version streaming de la résolution AoC avec o3.
    Affiche en temps réel + retourne la réponse finale.
    """

    final_answer = []
    client = OpenAI()
    # 🔥 Utilisation de responses.stream (contexte recommandé)
    with client.responses.stream(
        model="o5",  # modèle de raisonnement haut de gamme pour maths / logique / code
        input=[
            {
                "role": "developer",
                "content": (
                    "En tant qu'expert en algorithmique et Advent of Code, "
                    "résous le problème donné de manière concise et correcte. "
                    "Pas d'explications, donne juste la réponse finale."
                    "En utilisant l'input envoyé."
                ),
            },
            {
                "role": "user",
                "content": problem_statement,
            },
        ],
        reasoning={"effort": "high"},  # contrôle l'effort de raisonnement low, medium ou high
    ) as stream:

        # Boucle sur les events SSE
        for event in stream:
            # Event de texte incrémental
            if event.type == "response.output_text.delta":
                # event.delta contient le morceau de texte
                chunk = event.delta
                print(chunk, end="", flush=True)
                final_answer.append(chunk)

            # Tu peux aussi logger d'autres types si tu veux débug :
            # elif event.type == "response.error":
            #     print("ERROR:", event.error)

        # Récupère la réponse finale complète si besoin
        response = stream.get_final_response()

    return "".join(final_answer) or getattr(response, "output_text", str(response))

def solve_advent_of_code(problem_statement: str) -> str:
    """
    Envoie un énoncé de problème (type Advent of Code) au modèle de raisonnement o3
    et renvoie la réponse textuelle.

    :param problem_statement: Énoncé complet du problème, éventuellement avec l'input.
    :return: Réponse textuelle générée par le modèle.
    """
    
    client = OpenAI()

    response = client.responses.create(
        model="o3",  # modèle de raisonnement haut de gamme pour maths / logique / code
        input=[
            {
                "role": "developer",
                "content": (
                    "Tu es un expert en algorithmique, compétitions de programmation "
                    "et Advent of Code. Donne une réponse correcte et concise au problème. "
                    "Si des hypothèses sont nécessaires, explique-les brièvement."
                ),
            },
            {
                "role": "user",
                "content": problem_statement,
            },
        ],
        # Optionnel : contrôler l'effort de raisonnement (si exposé sur ton compte)
        reasoning={"effort": "medium"},  # 'low' | 'medium' | 'high'
    )

    # Selon les SDK récents, tu peux souvent faire :
    # return response.output_text
    # mais pour être robuste, on reconstruit à partir de output:
    parts = []
    for item in getattr(response, "output", []):
        for content in getattr(item, "content", []):
            if getattr(content, "type", None) == "output_text":
                parts.append(content.text)

    # Fallback si output_text existe directement
    if hasattr(response, "output_text") and not parts:
        return response.output_text

    return "\n".join(parts) if parts else str(response)

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

# Exemple d'utilisation
if __name__ == "__main__":
    url = "https://adventofcode.com/2025/day/3"
    selector = "article.day-desc"  # ex: récupérer tous les <p>

    text = scrape_text(url, selector)
    input_text = read_text_file("input.txt")
    prompt = f"Resolve this problem: {text}\n\nInput:\n{input_text}"
    print( "Prompt envoyé au modèle, attente de reponse..." )
    result = solve_advent_of_code_stream(prompt)
    print(result)

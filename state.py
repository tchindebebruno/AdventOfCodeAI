from playwright.sync_api import sync_playwright

# URL d'une page sur laquelle tu dois être connecté (login ou zone privée)
SITE_URL = "https://adventofcode.com"  # 🔁 À adapter

# Dossier où Playwright va stocker son "profil Edge-like"
PROFILE_DIR = "playwright_edge_profile"   # un dossier local au projet

def main():
    with sync_playwright() as p:
        # On utilise un contexte PERSISTANT, mais avec un profil à nous
        context = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,   # on veut voir la fenêtre pour se connecter
        )

        page = context.new_page()
        page.goto(SITE_URL)

        print("💡 Une fenêtre de navigateur vient de s'ouvrir.")
        print("   Connecte-toi normalement sur le site (login, 2FA, etc.).")
        input("➡️ Quand tu es bien connecté et que la page est OK, appuie sur Entrée ici...")

        # Sauvegarde des cookies + storage dans un fichier
        context.storage_state(path="edge_state.json")
        print("✅ Session sauvegardée dans edge_state.json")

        context.close()

if __name__ == "__main__":
    main()

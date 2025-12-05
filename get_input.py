from playwright.sync_api import sync_playwright

AUTH_URL = "https://adventofcode.com/2025/day/4/input"  # À adapter

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="edge_state.json")

        page = context.new_page()

        # ici on récupère la réponse principale
        response = page.goto(AUTH_URL)

        page.wait_for_timeout(2000)

        if response:
            print("✅ Statut HTTP :", response.status)
        else:
            print("❓ Impossible d'obtenir la réponse principale")

        print("🌐 URL finale :", page.url)
        print("\n--- HTML (2000 chars) ---\n")
        print(page.content()[:2000])

        browser.close()

if __name__ == "__main__":
    main()

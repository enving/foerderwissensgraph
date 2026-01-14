import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright


async def test_formularschrank_access():
    """
    Erster Discovery-Test für den BMWK Formularschrank.
    Prüft Erreichbarkeit und extrahiert erste Dokumenten-Links.
    """
    async with async_playwright() as p:
        print("🚀 Starte Discovery-Test (Headless Chromium)...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # BMWK Formularschrank (Beispiel-Ministerium)
        # Hinweis: Im System oft noch als 'bmwe' (Wirtschaft und Energie) geführt
        url = "https://foerderportal.bund.de/easy/easy_index.php?auswahl=formularschrank_foerderportal&formularschrank=bmwe"
        print(f"🔗 Verbinde mit: {url}")

        try:
            # Erhöhtes Timeout für langsame Bundes-Server
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Warte kurz auf JS-Inhalte
            await page.wait_for_timeout(2000)

            print(f"✅ Seite geladen: {await page.title()}")

            # Extrahiere alle Links
            links = await page.query_selector_all("a")
            print(f"📊 Insgesamt {len(links)} Links auf der Seite gefunden.")

            # Klicke auf 'Zuwendungen auf Ausgabenbasis (AZA)'
            print("🖱️ Öffne Kategorie: Zuwendungen auf Ausgabenbasis (AZA)...")
            # Wir versuchen es über den Text-Selektor
            await page.click("text='Zuwendungen auf Ausgabenbasis (AZA)'")
            await page.wait_for_timeout(5000)  # Mehr Zeit für den Bundes-Server

            # Prüfe ob neue Inhalte da sind (z.B. Tabellen-ID 't1')
            table_visible = await page.is_visible("#t1")
            print(f"🧐 Tabelle 't1' sichtbar: {table_visible}")

            if not table_visible:
                print(
                    "⚠️  Tabelle nicht sichtbar. Versuche direkten JavaScript-Aufruf..."
                )
                await page.evaluate("easy_tabelle('t1', 7)")
                await page.wait_for_timeout(5000)
                table_visible = await page.is_visible("#t1")
                print(f"🧐 Tabelle 't1' nach Evaluation sichtbar: {table_visible}")

            if table_visible:
                # Extrahiere strukturierte Daten aus der Tabelle
                rows = await page.query_selector_all("#t1 tr")
                print(f"📊 {len(rows)} Zeilen in Tabelle gefunden.")

                pdf_documents = []
                for row in rows:
                    cells = await row.query_selector_all("td")
                    if len(cells) >= 3:
                        nr = await cells[0].inner_text()
                        title = await cells[1].inner_text()
                        file_link = await cells[2].query_selector("a")

                        if file_link:
                            href = await file_link.get_attribute("href")
                            filename = await file_link.inner_text()

                            if href:
                                full_url = (
                                    href
                                    if href.startswith("http")
                                    else f"https://foerderportal.bund.de/easy/{href}"
                                )
                                pdf_documents.append(
                                    {
                                        "nr": nr.strip(),
                                        "title": title.strip(),
                                        "filename": filename.strip(),
                                        "url": full_url,
                                    }
                                )

            # Zeige die ersten 10 Treffer
            print(f"\n📄 {len(pdf_documents)} Dokumente erfolgreich identifiziert:")
            for i, doc in enumerate(pdf_documents[:10], 1):
                print(f"   {i}. [{doc['nr']}] {doc['title']} ({doc['filename']})")
                # print(f"      URL: {doc['url']}")

            if pdf_documents:
                print("\n✨ Discovery-Test erfolgreich abgeschlossen.")
            else:
                print(
                    "\n⚠️  Keine Dokumente gefunden. Möglicherweise hat sich die Struktur geändert."
                )

        except Exception as e:
            print(f"❌ Fehler während der Discovery: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_formularschrank_access())

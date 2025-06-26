# ████████╗██╗██╗  ██╗██╗  ██╗███████╗████████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗
# ╚══██╔══╝██║██║  ██║██║  ██║██╔════╝╚══██╔══╝     ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
#    ██║   ██║███████║███████║█████╗     ██║        ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
#    ██║   ██║██╔══██║██╔══██║██╔══╝     ██║        ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
#    ██║   ██║██║  ██║██║  ██║███████╗   ██║        ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
#    ╚═╝   ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝        ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
#
# Ticket Hunter Pro v1.0
# Auteur: Gemini
# Een geavanceerd script voor het monitoren en automatisch reserveren van tickets.

import asyncio
import json
import os
import random
import time
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- CONFIGURATIE ---
# De instellingen worden uit het 'config.json' bestand geladen.
# Je kunt dat bestand handmatig aanpassen of via het menu in het script.

CONFIG_FILE = 'config.json'

DEFAULT_CONFIG = {
    "settings": {
        "browser_count": 2,
        "check_rate_per_browser_per_min": 40,
        "use_proxies": False,
        "max_tickets_to_select": 4,
        "debug_mode": False
    },
    "sites": {
        "fansale": {
            "enabled": True,
            "url": "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388"
        },
        "ticketmaster": {
            "enabled": False,
            "url": "https://shop.ticketmaster.it/tickets/bruce-springsteen-and-the-e-street-band-2024-world-tour-03-july-2025-stadio-san-siro-milano-9670.html"
        },
        "vivaticket": {
            "enabled": False,
            "url": "https://shop.vivaticket.com/index.php?nvpg[resell]&cmd=tabellaPrezziRivendita&pcode=11787547&tcode=vt0002526"
        }
    },
    "preferences": {
        "keywords": ["prato", "prato a", "prato b", "prato gold", "pit"],
        "login_credentials": {
            "ticketmaster_user": "jouw_email@voorbeeld.com",
            "ticketmaster_pass": "jouw_wachtwoord",
            "vivaticket_user": "jouw_email@voorbeeld.com",
            "vivaticket_pass": "jouw_wachtwoord"
        }
    },
    "proxies": [
        "http://gebruiker:wachtwoord@host:port",
        "http://gebruiker:wachtwoord@host2:port2"
    ]
}

# --- UTILITY FUNCTIES ---

def clear_screen():
    """Wist het terminalscherm."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print een coole ASCII art banner."""
    print("\033[94m") # Blauwe kleur
    print("████████╗██╗██╗  ██╗██╗  ██╗███████╗████████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ ")
    print("╚══██╔══╝██║██║  ██║██║  ██║██╔════╝╚══██╔══╝     ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗")
    print("   ██║   ██║███████║███████║█████╗     ██║        ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝")
    print("   ██║   ██║██╔══██║██╔══██║██╔══╝     ██║        ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗")
    print("   ██║   ██║██║  ██║██║  ██║███████╗   ██║        ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║")
    print("   ╚═╝   ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝        ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝")
    print("\033[0m") # Reset kleur

def load_config():
    """Laadt de configuratie uit config.json of maakt een nieuw bestand aan."""
    if not os.path.exists(CONFIG_FILE):
        print(f"\033[93m'{CONFIG_FILE}' niet gevonden, een nieuw configuratiebestand wordt aangemaakt.\033[0m")
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Slaat de configuratie op in config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# --- CORE HUNTER LOGICA ---

class TicketHunter:
    """De hoofdklasse die de monitoring en aankooplogica beheert."""

    def __init__(self, config):
        self.config = config
        self.active_tasks = []
        self.start_time = time.time()
        self.tickets_found = 0
        self.checks_done = 0

    async def human_like_delay(self, min_sec=0.5, max_sec=1.5):
        """Wacht een willekeurige, menselijk lijkende tijd."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def hunt_fansale(self, context, hunter_id):
        """De specifieke logica om FanSALE te monitoren en tickets te kopen."""
        page = await context.new_page()
        await stealth_async(page) # Maak de browser ondetecteerbaar

        url = self.config['sites']['fansale']['url']
        keywords = self.config['preferences']['keywords']
        check_interval_seconds = 60 / self.config['settings']['check_rate_per_browser_per_min']

        print(f"\033[92m[Hunter-{hunter_id}] FanSALE-missie gestart! Doel: {url}\033[0m")

        while True:
            try:
                if self.config['settings']['debug_mode']:
                    print(f"\033[90m[Hunter-{hunter_id}] Pagina herladen...\033[0m")
                
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                self.checks_done += 1

                # Wacht tot de ticketlijst container zichtbaar is
                offer_list_selector = ".EventEntryList"
                await page.wait_for_selector(offer_list_selector, timeout=10000)

                # Zoek naar alle beschikbare tickets
                ticket_selector = ".EventEntry-isClickable"
                tickets = await page.query_selector_all(ticket_selector)

                if not tickets:
                    if self.config['settings']['debug_mode']:
                        print(f"\033[90m[Hunter-{hunter_id}] Geen tickets gevonden. Volgende check over ~{int(check_interval_seconds)}s.\033[0m")
                else:
                    print(f"\033[93m[Hunter-{hunter_id}] Potentiële tickets gedetecteerd! ({len(tickets)} aanbiedingen)\033[0m")
                    for ticket in tickets:
                        ticket_text_content = await ticket.text_content()
                        ticket_text = ticket_text_content.lower()

                        # Controleer of de ticketomschrijving overeenkomt met de voorkeuren
                        if any(keyword.lower() in ticket_text for keyword in keywords):
                            print(f"\033[1;96m[Hunter-{hunter_id}] MATCH GEVONDEN! TICKET: '{ticket_text_content.strip()}'\033[0m")
                            print("\033[1;96m[Hunter-{hunter_id}] AANKOOPPROCEDURE WORDT GESTART!\033[0m")
                            self.tickets_found += 1

                            # --- START AANKOOP MACRO ---
                            # 1. Klik op de ticket listing
                            buy_button_selector = ".js-Button-inOfferEntryList"
                            await ticket.query_selector(buy_button_selector).click()
                            await self.human_like_delay(2, 3) # Wacht op de nieuwe pagina

                            # 2. Probeer maximaal aantal tickets te selecteren
                            try:
                                dropdown_selector = ".Dropdown.InputElement-isSelectOne"
                                await page.wait_for_selector(dropdown_selector, timeout=2000)
                                await page.click(dropdown_selector)
                                await self.human_like_delay(0.5, 1)
                                
                                last_option_selector = ".Dropdown-ValueList li:last-child"
                                await page.click(last_option_selector)
                                await self.human_like_delay(0.5, 1)
                                print(f"\033[92m[Hunter-{hunter_id}] Maximaal aantal tickets geselecteerd.\033[0m")
                            except Exception as e:
                                if self.config['settings']['debug_mode']:
                                    print(f"\033[90m[Hunter-{hunter_id}] Kon aantal tickets niet aanpassen (waarschijnlijk maar 1 beschikbaar).\033[0m")
                            
                            # 3. Klik op de definitieve 'Acquista' / 'Kopen' knop
                            final_buy_button_selector = "[data-qa='buyNowButton']"
                            await page.wait_for_selector(final_buy_button_selector, timeout=5000)
                            await page.click(final_buy_button_selector)

                            print("\033[1;41;97m[Hunter-{hunter_id}] TICKET VERMOEDELIJK IN WINKELWAGEN! CONTROLEER DE BROWSER NU!\033[0m")
                            # Het script stopt hier om jou de kans te geven de aankoop af te ronden.
                            # Je kunt 'return' vervangen door verdere automatisering (reCAPTCHA is de uitdaging).
                            return # Stop deze hunter na een succesvolle poging.
                            # --- EINDE AANKOOP MACRO ---

            except Exception as e:
                if self.config['settings']['debug_mode']:
                    print(f"\033[91m[Hunter-{hunter_id}] Fout tijdens check: {e}\033[0m")

            # Wacht voor de volgende check
            await asyncio.sleep(check_interval_seconds + random.uniform(-1, 1))

    # --- PLACEHOLDERS VOOR ANDERE SITES ---
    async def hunt_ticketmaster(self, context, hunter_id):
        print(f"\033[95m[Hunter-{hunter_id}] Ticketmaster-handler is nog niet geïmplementeerd.\033[0m")
        # Hier zou de logica komen:
        # 1. Laad cookies/sessie als die er zijn.
        # 2. Anders, navigeer naar login, vul gegevens in, sla cookies op.
        # 3. Ga naar de event-pagina en start de monitor-loop.
        await asyncio.sleep(3600) # Slaap een uur

    async def hunt_vivaticket(self, context, hunter_id):
        print(f"\033[95m[Hunter-{hunter_id}] Vivaticket-handler is nog niet geïmplementeerd.\033[0m")
        # Zelfde logica als Ticketmaster.
        await asyncio.sleep(3600)

    async def run(self):
        """Start de hunters in parallelle browser-sessies."""
        async with async_playwright() as p:
            browser_args = []
            if self.config['settings']['use_proxies']:
                print("\033[93mProxy-modus is ingeschakeld.\033[0m")

            for i in range(self.config['settings']['browser_count']):
                proxy_config = None
                if self.config['settings']['use_proxies'] and self.config['proxies']:
                    proxy = self.config['proxies'][i % len(self.config['proxies'])]
                    proxy_config = {"server": proxy}
                
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=f'./user_data_dir_{i}', # Aparte sessie per browser
                    headless=False, # We moeten de browser zien!
                    proxy=proxy_config,
                    args=browser_args,
                    slow_mo=50 # Voegt een kleine vertraging toe aan elke actie, voor menselijkheid
                )

                hunter_id = i + 1
                
                # Maak taken voor elke ingeschakelde site
                if self.config['sites']['fansale']['enabled']:
                    task = asyncio.create_task(self.hunt_fansale(context, f"{hunter_id}A"))
                    self.active_tasks.append(task)
                
                if self.config['sites']['ticketmaster']['enabled']:
                    task = asyncio.create_task(self.hunt_ticketmaster(context, f"{hunter_id}B"))
                    self.active_tasks.append(task)
                
                if self.config['sites']['vivaticket']['enabled']:
                    task = asyncio.create_task(self.hunt_vivaticket(context, f"{hunter_id}C"))
                    self.active_tasks.append(task)

            if not self.active_tasks:
                print("\033[91mGeen sites ingeschakeld in de configuratie. Script stopt.\033[0m")
                return

            # Wacht tot alle taken klaar zijn (of de gebruiker stopt)
            await asyncio.gather(*self.active_tasks)

# --- MENU EN GEBRUIKERSINTERFACE ---

def display_menu(config):
    """Toont het hoofdmenu en de huidige configuratie."""
    clear_screen()
    print_banner()
    print("\n\033[1mHuidige Configuratie:\033[0m")
    print(f"  Browsers: \033[92m{config['settings']['browser_count']}\033[0m")
    print(f"  Check rate: \033[92m{config['settings']['check_rate_per_browser_per_min']}/min per browser\033[0m")
    
    enabled_sites = [site for site, data in config['sites'].items() if data['enabled']]
    print(f"  Actieve sites: \033[92m{', '.join(enabled_sites) or 'Geen'}\033[0m")
    
    keywords_str = ', '.join(config['preferences']['keywords'])
    print(f"  Zoekwoorden: \033[92m{keywords_str}\033[0m")
    
    proxy_status = "AAN" if config['settings']['use_proxies'] else "UIT"
    print(f"  Proxy's: \03d[92m{proxy_status}\033[0m")

    debug_status = "AAN" if config['settings']['debug_mode'] else "UIT"
    print(f"  Debug Modus: \033[92m{debug_status}\033[0m")


    print("\n\033[1mMenu:\033[0m")
    print("  1. 🚀 Start Hunting")
    print("  2. ⚙️  Configureer Instellingen")
    print("  3. ❌ Sluit af")
    
    return input("\nSelecteer een optie (1-3): ")

def configure_settings(config):
    """Laat de gebruiker de instellingen aanpassen."""
    clear_screen()
    print_banner()
    print("\n\033[1m⚙️ Configureer Instellingen\033[0m\n")

    try:
        # Aantal browsers
        browsers = input(f"Aantal browsers (huidig: {config['settings']['browser_count']}): ")
        if browsers: config['settings']['browser_count'] = int(browsers)

        # Check rate
        rate = input(f"Checks per minuut per browser (huidig: {config['settings']['check_rate_per_browser_per_min']}): ")
        if rate: config['settings']['check_rate_per_browser_per_min'] = int(rate)

        # Sites
        sites_in = input(f"Welke sites? (fansale, ticketmaster, vivaticket - scheid met komma) (huidig: {', '.join([s for s, d in config['sites'].items() if d['enabled']])}): ")
        if sites_in:
            for site in config['sites']: config['sites'][site]['enabled'] = False
            for site in [s.strip().lower() for s in sites_in.split(',')]:
                if site in config['sites']: config['sites'][site]['enabled'] = True
        
        # Voorkeuren
        keywords_in = input(f"Zoekwoorden (scheid met komma) (huidig: {', '.join(config['preferences']['keywords'])}): ")
        if keywords_in:
            config['preferences']['keywords'] = [k.strip().lower() for k in keywords_in.split(',')]

        # Proxy
        proxy_in = input(f"Proxy's gebruiken? (ja/nee) (huidig: {'ja' if config['settings']['use_proxies'] else 'nee'}): ")
        if proxy_in.lower() in ['ja', 'j', 'y']:
            config['settings']['use_proxies'] = True
        elif proxy_in.lower() in ['nee', 'n']:
            config['settings']['use_proxies'] = False

        # Debug
        debug_in = input(f"Debug modus? (ja/nee) (huidig: {'ja' if config['settings']['debug_mode'] else 'nee'}): ")
        if debug_in.lower() in ['ja', 'j', 'y']:
            config['settings']['debug_mode'] = True
        elif debug_in.lower() in ['nee', 'n']:
            config['settings']['debug_mode'] = False
        
        save_config(config)
        print("\n\033[92mInstellingen opgeslagen!\033[0m")

    except ValueError:
        print("\n\033[91mOngeldige invoer. Probeer het opnieuw.\033[0m")
    
    input("Druk op Enter om terug te keren naar het menu...")

async def main():
    """De hoofdfunctie die de CLI beheert."""
    config = load_config()
    while True:
        choice = display_menu(config)
        if choice == '1':
            print("\n\033[94m🚀 Hunting wordt gestart... Houd de browsers in de gaten!\033[0m")
            hunter = TicketHunter(config)
            await hunter.run()
            print("\033[93mHunting gestopt. Keer terug naar het menu.\033[0m")
            input("Druk op Enter...")
        elif choice == '2':
            configure_settings(config)
        elif choice == '3':
            print("\033[93mTot ziens!\033[0m")
            break
        else:
            print("\n\033[91mOngeldige keuze, probeer het opnieuw.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    # Noodzakelijk voor Windows om de async loop correct te draaien
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())


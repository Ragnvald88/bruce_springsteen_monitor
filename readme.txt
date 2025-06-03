I have added the details for the event that has to be monitored under ===monitoring=== including my login credentials
Also my proxy residential server information is under ===Proxy===


===Proxy====
IpRoyal: Residential Proxy:
proxy dashboard:
https://dashboard.iproyal.com/products/royal-residential-proxies
Hostname: geo.iproyal.com
Port: 12321
Username: Doqe2Sm9Yjl1MrZd
Password: Xqw3HOkEcUw7Vv3i

====Monitoring====
Ticketmaster:
E-mail: ronaldhoogenberg@#gmail.com
Password: Hagappoq221!
Event links: https://shop.ticketmaster.it/tickets/bruce-springsteen-and-the-e-street-band-2024-world-tour-03-july-2025-stadio-san-siro-milano-9670.html

Fansale:
E-mail: ronaldhoogenberg@hotmail.com
Password: Hagappoq221!
Event link: https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844201

Vivaticket
Email: ronaldhoogenberg@gmail.com
Password: Hagappoq221!
https://shop.vivaticket.com/index.php?nvpg[resell]&cmd=tabellaPrezziRivendita&pcode=11787547&tcode=vt0002526

2captcha.com 
API: c58050aca5076a2a26ba2eff1c429d4d


profielen openen 
Golden profile
python src/main.py --warm-profile "P03_MacOS15_Chrome125_M4Pro_NL" --start-url "https://www.google.it"



https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388


bash# Pre-authenticate profiles
python src/main.py --warm-profile 

# Run beast mode
python src/main.py --beast

# Check logs
tail -f logs/beast_mode.log

# Monitor detections
tail -f logs/detections.log | grep "DETECTED"

# Emergency stop
Ctrl+C (twice for force quit)
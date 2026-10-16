# PokéRadar LIVE — gehoste sealed-productmonitor

Een deploybaar project voor **GitHub Pages + GitHub Actions**. De website is publiek bereikbaar. De automatische controle loopt **elk uur** op GitHub, ook als jouw telefoon of browser uit staat. De monitor ondersteunt productpagina's met **schema.org JSON-LD Product/Offer** in EUR. Bij ontbrekende of geblokkeerde data toont hij eerlijk *Niet te verifiëren*. Geen prijsvermelding is een garantie.

## Live zetten (ongeveer 10 stappen)

1. Maak een GitHub-account aan indien nodig.
2. Maak een **nieuwe, publieke repository**, bijvoorbeeld `pokeradar` (GitHub Pages op gratis accounts werkt eenvoudig in openbare repositories).
3. Upload de **inhoud van deze ZIP** naar de **root** van de repository, inclusief de verborgen map `.github/workflows/`. Laat de hoofdbranch `main` heten.
4. Ga naar **Settings → Pages → Build and deployment → Source: GitHub Actions**.
5. Open **Actions → Publiceer PokéRadar website → Run workflow**. Daarna verschijnt je adres in Settings → Pages, normaal `https://GEBRUIKERSNAAM.github.io/pokeradar/`.
6. Open **Actions → PokéRadar prijs- en voorraadcontrole → Run workflow** voor de eerste meting. Vervolgmetingen volgen automatisch ieder uur (rond minuut 17 UTC; GitHub kan vertraagd uitvoeren).
7. Voeg in `products.json` de **rechtstreekse HTTPS-productpagina's** van winkels toe die jij vertrouwt; wijzig per product `max_price`. Gebruik unieke `id`-waarden. Niet een zoekpagina, categoriepagina of vergelijkingssite toevoegen: de monitor vereist Product/Offer-gegevens.
8. Voor pushachtige meldingen via Telegram: maak met `@BotFather` een Telegram-bot aan; bewaar de verkregen bot-token privé. Stuur je eigen bot `/start`. Zoek vervolgens je chat-ID via de Telegram Bot API of een chat-ID-tool die je vertrouwt.
9. Ga naar **Settings → Secrets and variables → Actions → New repository secret**, voeg `TELEGRAM_BOT_TOKEN` en `TELEGRAM_CHAT_ID` toe. **Zet secrets nooit in products.json, HTML of een commit.**
10. Bij een **prijsdaling**, **nieuwe voorraad na uitverkocht**, of **een prijs die onder jouw ingestelde limiet zakt**, verstuurt de monitor een Telegram-bericht. De eerste meting is een beginwaarde en verstuurt opzettelijk nog geen alarm.

## Wat werkt wel en niet?

- ✅ Gehost dashboard inclusief je vorige persoonlijke verzameltracker (`collector.html`).
- ✅ Uurlijkse geplande controles (mits repository/Actions actief blijven); ook dagelijks.
- ✅ Prijsdaling, restock en maxprijs-alerts (Telegram secrets nodig).
- ✅ Bronlink, tijdstip en duidelijke status.
- ⚠️ Er zit **1 voorbeeldproductlink** in `products.json`, niet een volledig automatisch ontdekte database van alle webshops. Voeg meer links toe; vergelijk eerst de betrouwbaarheid van de shop.
- ⚠️ Niet elke webshop publiceert bruikbare JSON-LD of staat automatische downloads toe. De monitor markeert die pagina als **unverifiable**. Er wordt nooit een prijs geraden.
- ⚠️ Dit script leest geen dynamische JavaScript-prijzen, versendkosten of couponcodes en logt niet in op webshops. Een 'in stock'-melding is afhankelijk van de door de webshop gepubliceerde data. Respecteer robots.txt en voorwaarden van de retailers; bij blokkades de bron verwijderen of hun officiële API gebruiken.
- ⚠️ De GitHub Pages-site is openbaar, inclusief `products.json` en historische status. Je persoonlijke collectie blijft lokaal in de browser. Telegram-gegevens blijven in GitHub Secrets.
- ⚠️ Inactieve publieke repositories kunnen na 60 dagen hun geplande workflows automatisch uitgeschakeld krijgen, en Github kan controles vertragen.
- ⚠️ GitHub Pages is een openbare website, **geen besloten server met accounts**. Verder bouwen met een backend/database is nodig als je per gebruiker privé instellingen of onbeperkt winkels wilt volgen.

## Technisch

```
site/index.html      dashboard
site/collector.html  bestaande verzameling-app
site/radar.json      laatst gemeten dashboarddata
products.json        te controleren productpagina's + persoonlijke prijslimieten
monitor/check.py     JSON-LD-prijslezer + Telegram-alerts
.github/workflows/   geplande monitor + automatische Pages-deployment
data/state.json      vorige metingen voor verschillen
```

Manueel uitvoeren: `python monitor/check.py` (vereist internet om winkels te bezoeken). Losse parser-test: `python -m unittest discover -s tests`.

## Belangrijk

De code is een direct te uploaden, complete starter die lokaal is gecontroleerd op syntaxis en parser-logica. Ik heb **niet** op jouw GitHub-account gedeployed, Telegram ingesteld of een werkende live-alert afgeleverd: daarvoor zijn jouw account en persoonlijke secrets vereist.

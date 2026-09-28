# Arqen

[![Release](https://img.shields.io/github/v/release/stefansemb/Arqen?color=b7ff18&labelColor=101214)](https://github.com/stefansemb/Arqen/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-b7ff18?labelColor=101214)](LICENSE)
[![Windows 10 and 11](https://img.shields.io/badge/Windows-10%20%7C%2011-b7ff18?labelColor=101214)](#kom-igång)
[![Discussions](https://img.shields.io/github/discussions/stefansemb/Arqen?color=b7ff18&labelColor=101214)](https://github.com/stefansemb/Arqen/discussions)

Arqen är en lokal AI-assistent för Windows, byggd med PyQt6, med ett
**Kontrollrum** för agenter, uppgifter och arbetsflöden. Gränssnittet och rösten
finns på engelska (standard) och svenska; välj under Inställningar → Språk.
Designen är mörk med limegröna accenter.

*[English](README.md)*

![Arqen: en chatt, med en agents Telegram-inlägg som väntar på godkännande överst](docs/images/chat.png)

*Skärmbilderna visar demodata och det engelska gränssnittet.*

Arqen är byggt för att vara lokalt, kontrollerbart och utbyggbart. Molnmodeller
är valfria; lokal körning via Ollama eller LM Studio fungerar som grund. Allt som
inte går att ångra kräver ditt godkännande.

> Arqen växte fram ur en tidigare app, Arqen Desktop, som inte utvecklas
> längre; dess sista version finns kvar som taggen `arqen-desktop-legacy`.

## Funktioner

**Chatt och röst**

- Chattlista med öppna, byt namn och ta bort; streaming och avbrytning.
- Neural röst via Edge TTS (`sv-SE-MattiasNeural` på svenska,
  `en-GB-RyanNeural` på engelska) och taligenkänning via faster-whisper.
- Röstpanel med en animerad ring som visar om Arqen vilar, lyssnar, tänker eller
  pratar. Färgerna kan ändras i `config/arqen.json`.
- Statistikpanel med tokens och kostnad för chatten, senaste svaret och totalt.

**Kontrollrum**

![Agenterna i Kontrollrummet](docs/images/agents.png)

- Uppgifter, arbetsflöden med flera agenter, scheman och aktivitetslogg.
- Agenter med egna verktygsregler. Varje uppgift körs i en egen, fristående
  Arqen, så en agents begränsningar aldrig påverkar chatten.
- Timeout, återhämtning, försök igen och sparade resultat för uppgifter.
- En godkännanderad överst i alla vyer samlar allt som väntar på dig.

**Minne**

- Långtidsminne med källa, status och säkerhet.
- Arqen **föreslår** minnen när du berättar något bestående; du godkänner eller
  avvisar dem under Minne. Bara godkända minnen används.
- **Reflektera**: Arqen läser senaste uppgifter och chattar och föreslår
  bestående lärdomar, också de som förslag.
- Relevanta minnen väljs ut per meddelande när minnet växer.
- "Kom ihåg att …" sparar direkt.

**Verktyg och säkerhet**

![Tool Gatewayens katalog, med webbverktygen utfällda](docs/images/tools.png)

- Verktyg för system, fönster och program, filer i arbetsytan, dokument (PDF,
  Word, Excel), webben, en egen webbläsare, väder, röst och bildgenerering.
- Godkännande krävs för att skriva, ta bort, flytta eller ångra filer, skapa
  bilder (kostar pengar) och stänga program.
- Tool Gateway med risknivåer, regler per agent och en lokal logg över alla
  verktygsanrop, synliga under Verktyg.
- Minnen som ser ut som lösenord eller nycklar sparas aldrig.

**Anslutningar**

![Anslutningar: ge en agent tillgång till paket av verktyg](docs/images/connections.png)

- Ge en agent tillgång till paket av verktyg med ett klick per kort.
- **GitHub** (personlig token): repon, issues och pull requests; att skapa en
  issue kräver godkännande.
- **Google** (OAuth med egen Desktop-klient): söka och läsa Gmail, se kommande
  händelser i Kalender, söka och läsa filer i Drive. Mejlutkast och
  kalenderhändelser skapas med godkännande; inget mejl skickas.
- **Discord** (webhook) och **Telegram** (bot): skicka meddelanden med
  godkännande, och valfria aviseringar när uppgifter blir klara eller misslyckas.
- **MCP-servrar**: lägg till en adress (t.ex. Zapiers MCP-URL) eller ett lokalt
  program; serverns verktyg blir Arqen-verktyg. De kräver godkännande om servern
  inte märker dem som endast läsande.
- Nycklar sparas i `config/arqen-secrets.json`, läses först när ett verktyg körs
  och rensas bort ur allt verktygen svarar.

**Modeller**

- Ollama/LM Studio, OpenRouter, OpenAI, Gemini, Claude och Arqen Remote.
- Färdiga profiler: Privat (Ollama), Snabb (OpenRouter), Viktigt (OpenAI) och
  Kreativt (Gemini).
- Valfri reservprovider om den första inte svarar (avstängd som standard).

## Kom igång

### Det här behöver du

- En dator med **Windows 10 eller 11** och ungefär **1,5 GB** ledigt
  diskutrymme.
- Internetanslutning medan du installerar.
- En modell som Arqen tänker med, något av:
  - en **API-nyckel** från [OpenRouter](https://openrouter.ai/keys),
    [OpenAI](https://platform.openai.com/api-keys),
    [Google Gemini](https://aistudio.google.com/apikey) eller
    [Anthropic](https://console.anthropic.com/settings/keys), eller
  - **[Ollama](https://ollama.com)**: gratis och helt lokalt på din egen
    dator (kräver en hyfsat snabb dator).

Du behöver inte installera Python själv: installationsprogrammet sköter det.

### Installera (5 till 10 minuter)

1. Öppna [senaste versionen](https://github.com/stefansemb/Arqen/releases/latest)
   och klicka på **Source code (zip)** under **Assets**.
2. Gå till mappen **Hämtade filer**, högerklicka på zip-filen och välj
   **Extrahera alla…**. Välj mappen **Dokument** och klicka på **Extrahera**.
   Du får en mapp som heter **Arqen-** och versionsnumret, till exempel
   **Arqen-1.0.1**; där bor Arqen.
3. Öppna den mappen och dubbelklicka på **`install.cmd`**.
   - *"Datorn skyddades av Windows"*: klicka på **Mer information** och sedan
     **Kör ändå**.
   - *"Vill du köra den här filen?"*: klicka på **Kör**.
4. Ett svart fönster öppnas och gör jobbet. Det ställer några frågor på
   engelska; tryck **Enter** för att svara ja:
   - *Install Python 3.12?* (bara om du saknar det)
   - *Install ffmpeg?* (behövs för rösten; bara om du saknar det)
   - *Put a shortcut on the desktop too?* (genväg på skrivbordet)
   - *Start Arqen now?* (starta Arqen nu)
5. När det står **Arqen is installed**, tryck på valfri tangent för att stänga
   fönstret.

### Första starten (2 minuter)

1. Starta **Arqen** från Start-menyn eller skrivbordet.
2. Arqen startar på engelska. Klicka på **Settings** nere till vänster, välj
   fliken **Language**, välj **Svenska**, klicka på **SAVE** och sedan **Yes**
   när Arqen frågar om omstart. Öppna sedan **Inställningar** igen.
3. Välj en profil på fliken **Profil** och klicka på **TILLÄMPA PROFIL**:
   - *Snabb – OpenRouter*, *Viktigt – OpenAI* eller *Kreativt – Gemini* om du
     har den nyckeln, eller
   - *Privat – Ollama* för en lokal modell. Starta Ollama först och ladda ner
     en modell en gång: öppna en terminal och kör `ollama pull qwen3:8b`.
4. Klistra in nyckeln i **API-nyckel** på fliken **Leverantör** (behövs inte
   för Ollama). Klicka på **TESTA ANSLUTNING** och sedan **SPARA**.
5. Säg hej i **Chatt**. Prova *"Vad finns i min arbetsyta?"* eller
   *"Kom ihåg att jag vill ha korta svar."*

Arqen läser och skriver filer bara i sin arbetsyta. Välj mappen under
**Inställningar → Arbetsyta**; tomt betyder Arqens egen mapp.

### Uppdatera

1. Ladda ner och packa upp den nya versionen som ovan, i en **ny** mapp.
2. Kopiera mapparna **`config`** och **`data`** från den gamla Arqen-mappen
   till den nya. Där ligger dina inställningar, nycklar, chattar och minnen.
3. Dubbelklicka på **`install.cmd`** i den nya mappen. Genvägarna pekas då om
   till den. Ta sedan bort den gamla mappen.

### Avinstallera

Ta bort Arqen-mappen och Arqen-genvägarna (Start-menyn och skrivbordet). Om
installationen lade till Python eller ffmpeg kan du ta bort dem under
Windows **Inställningar → Appar**.

### Om något går fel

- **Arqen öppnas inte:** titta i `data\arqen.log` i Arqen-mappen, eller kör
  `install.cmd` igen.
- **"No supported Python was found"** och winget saknas: installera
  [Python 3.12](https://www.python.org/downloads/), kryssa i **Add python.exe
  to PATH** och kör `install.cmd` igen.
- **Arqen pratar inte:** ffmpeg saknas. Öppna en terminal, kör
  `winget install Gyan.FFmpeg`, logga sedan ut ur Windows och in igen.
- **TESTA ANSLUTNING misslyckas:** kontrollera nyckeln och att modellnamnet
  finns. För Ollama: kontrollera att Ollama körs och att modellen är
  nedladdad.

<details>
<summary>För utvecklare: installera för hand</summary>

Arqen kräver Python 3.10 till 3.13 (utvecklas på 3.12).

```powershell
git clone https://github.com/stefansemb/Arqen.git
cd Arqen
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m arqen.ui
```

- **ffmpeg** behöver finnas i `PATH` för rösten: `winget install Gyan.FFmpeg`.
- Inställningar sparas i `config/arqen.json` (`config/arqen.example.json` visar
  formatet) och nycklar i `config/arqen-secrets.json`. Ingen av dem checkas in.
- Chattar, minne, uppgifter och verktygsloggen ligger i `data/`; körs Arqen
  från genvägen hamnar dess meddelanden i `data/arqen.log`.
- Kärnan utan fönster startas med `python -m arqen`. Kontrollera en lokal
  provider med `python -m arqen.doctor`.

</details>

## Arqen i telefonen

Chatta med Arqen, godkänn verktyg och Kontrollrummets godkännanden och följ
dina uppgifter i telefonens webbläsare, medan Arqen körs på datorn.

![Arqen i telefonen: ett verktyg som väntar på godkännande, Kontrollrummets godkännanden och en uppgifts resultat](docs/images/phone.png)

1. Installera [Tailscale](https://tailscale.com) på datorn och telefonen och
   logga in med samma konto. Då når bara enheter i ditt eget tailnet Arqen;
   inget öppnas mot internet.
2. Öppna **Inställningar → Mobil** i Arqen och kryssa i *Låt min telefon nå
   Arqen*.
3. Skanna QR-koden med telefonens kamera och lägg sidan på hemskärmen.

QR-koden innehåller en token som ger full åtkomst till Arqen, så dela den
inte; **NY TOKEN** loggar ut alla telefoner. *Lokalt nätverk* fungerar utan
Tailscale för allt på samma wifi, och *Bara den här datorn* är till för att
prova sidan i en webbläsare. Ett verktyg som kräver godkännande visas som ett
kort med verktygets argument och **Godkänn** / **Avvisa**.

## Lokalt API

Telefonsidan pratar med Arqens API. Utan desktopappen kan det köras som en
egen process:

```powershell
python -m arqen.api --port 8765 --token <din-token>
```

Det lyssnar på `127.0.0.1` om inte `--host` säger annat, och vägrar alla
andra adresser utan token. Token kan också sättas med miljövariabeln
`ARQEN_API_TOKEN`; alla anrop utom `/api/v1/health` kräver då
`Authorization: Bearer <token>`. Kräver ett verktyg godkännande svarar ett
meddelande med `"status": "needs_confirmation"`, verktyget och dess
argument; svara med `POST /api/v1/sessions/{id}/confirmation` och
`{"approve": true}` eller `false`.

Endpoints under `/api/v1` finns för sessioner och meddelanden, status,
uppgifter, agenter, godkännanden, scheman, arbetsflöden och verktyg. Se
[MOBILE_API_PLAN.md](MOBILE_API_PLAN.md) för hela listan och vad som ännu inte
fungerar fullt ut.

## Utveckling

```powershell
python -m compileall -q arqen
python -m pytest -q
```

- `tests/conftest.py` pekar om arbetsytan och datakatalogen till en tillfällig
  mapp, så att tester aldrig rör dina chattar, minnen eller uppgifter. Ta inte
  bort den.
- All text i gränssnittet går via `tr()` i `arqen/ui/strings.py`: skriv den på
  engelska i koden och lägg den svenska översättningen i tabellen där, inte
  direkt i `window.py`. Språket väljs i Inställningar → Språk; engelska är
  standard.
- Nya verktyg behöver en kategori och ett namn på engelska och svenska i
  `arqen/ui/tool_catalog.py`; ett test kontrollerar det.

## Dokument

- [HANDOVER.md](HANDOVER.md) – aktuellt läge, beslut och nästa steg.
- [ARQEN_UI_DIRECTION.md](ARQEN_UI_DIRECTION.md) – riktning för gränssnittet.
- [HERMES_MISSION_CONTROL_PLAN.md](HERMES_MISSION_CONTROL_PLAN.md) – plan för
  Kontrollrummet och Hermes.
- [MOBILE_API_PLAN.md](MOBILE_API_PLAN.md) – API och framtida mobilklient.
- [DESIGN.md](DESIGN.md) och [FEATURE_INVENTORY.md](FEATURE_INVENTORY.md) –
  design- och funktionsbeslut.

## Status

Chatt, röst, Kontrollrum, Memory 2.0, Tool Gateway (med kostnad och
nyckelhantering) och anslutningarna (GitHub, Google, Discord, Telegram, MCP)
fungerar lokalt, och i telefonen via Tailscale.
Se HANDOVER för detaljer.

Frågor, idéer eller något att visa upp? Starta en tråd i
[Discussions](https://github.com/stefansemb/Arqen/discussions); fel rapporteras i
[Issues](https://github.com/stefansemb/Arqen/issues).

## Licens

[MIT](LICENSE) © 2026 Stefan Semb. Du får använda, ändra och dela Arqen,
även kommersiellt, så länge upphovsrättsraden och licensen följer med.

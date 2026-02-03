# CSGO / CS2 Skinport Sniper

Automates monitoring Skinport market pages and sends Discord alerts when items match your filters. A Chrome extension refreshes Skinport tabs, captures HTML, and posts it to a local Python server that parses listings, applies filters, and sends results to Discord. Filters can also be managed live via Discord bot commands.

## Features
- Sequentially refreshes multiple Skinport market tabs
- Captures page HTML and posts it to a local server
- Parses listings with price, float, and suggested price data
- Filter by skin name, max price, and max wear
- Discord alerts with deduplication
- Manage filters via Discord commands (`!add`, `!remove`, `!list`)

## Project Structure
- Chrome Extension 2.0/ — extension that refreshes tabs and sends HTML
- Skinport Sniper/LocalServerandBot.py — local server + parser + Discord bot
- Skinport Sniper/filters.json — saved filters
- Skinport Sniper/Parsing.py — standalone HTML parsing test script

## Requirements
- Python 3.10+
- Chrome/Chromium browser
- Python packages:
  - beautifulsoup4
  - lxml
  - pandas
  - discord.py

## Setup
1. Install Python dependencies.
2. Open Chrome Extensions and load the folder Chrome Extension 2.0/ as an unpacked extension.
3. In Skinport Sniper/LocalServerandBot.py:
   - Set your Discord bot token (`tok`).
   - Set your Discord channel ID in `bot.get_channel(...)`.
4. (Optional) Edit Skinport Sniper/filters.json to add initial filters.

## Usage
1. Start the Python server + Discord bot by running Skinport Sniper/LocalServerandBot.py.
2. Open one or more Skinport market tabs (https://skinport.com/market...).
3. The extension will refresh each tab in sequence and send HTML to the local server.
4. When listings match your filters, alerts are sent to Discord.

## Discord Commands
- `!add <Name> <Max Price> <Max Wear>` — add or update a filter
- `!remove <Name>` — remove a filter
- `!list` — show current filters

## Notes
- The parser expects prices in CA$ format (can be adjusted in code).
- Deduplication prevents sending the same alert repeatedly for the same tab.

## Disclaimer
This project is for educational use. Ensure you comply with Skinport’s terms of service and Discord’s developer policies please!!!

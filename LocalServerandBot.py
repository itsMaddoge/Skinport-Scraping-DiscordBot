import json
import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
import pandas as pd
import discord
from discord.ext import commands

# GLOBAL FILTERS ----------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
filters_file = os.path.join(script_dir, "filters.json")


# Load filters from file or initialize empty
try:
    with open(filters_file, 'r') as f:
        name_specific_filters = json.load(f)
except FileNotFoundError:
    name_specific_filters = {}

# Save filters to file
def save_filters():
    with open(filters_file, 'w') as f:
        json.dump(name_specific_filters, f, indent=4)

# HTML PARSER --------------------------------------------------------
def parse_html_and_create_dataframe(html):
    soup = BeautifulSoup(html, 'lxml')

    prices, suggested_prices, href_values, wears, names = [], [], [], [], []

    item_preview_elements = soup.find_all(class_="ItemPreview")

    for item_preview in item_preview_elements:
        href_element = item_preview.find('a', class_='ItemPreview-link')
        href_value = href_element['href'] if href_element else None

        price_element = item_preview.find(class_="ItemPreview-priceValue")
        price_value = price_element.find("div", class_="Tooltip-link").text

        wear_element = item_preview.find(class_="WearBar-value")
        wear_value = float(wear_element.text)

        suggested_price_element = item_preview.find(class_="ItemPreview-oldPrice")
        suggested_price = suggested_price_element.text

        suggested_price_parts = suggested_price.split(":")
        suggested_price = suggested_price_parts[1].strip() if len(suggested_price_parts) > 1 else suggested_price.strip()

        item_name_element = item_preview.find(class_="ItemPreview-itemName")
        item_name = item_name_element.text.strip() if item_name_element else "Unknown"

        # Append all the values
        wears.append(wear_value)
        prices.append(price_value)
        suggested_prices.append(suggested_price.replace('Suggested price', '').strip())
        href_values.append("https://skinport.com" + href_value)
        names.append(item_name)

    data = {'Name': names, 'Price': prices, 'Wear': wears, 'Suggested Price': suggested_prices, 'Href': href_values}
    df = pd.DataFrame(data)

    # Convert to a float
    df['Price'] = df['Price'].apply(lambda x: float(x.replace('CA$', '').replace(',', '')))
    df['Suggested Price'] = df['Suggested Price'].apply(lambda x: float(x.replace('CA$', '').replace(',', '')))

    df['Percent Difference'] = ((df['Price'] - df['Suggested Price']) / df['Suggested Price']) * 100

    # Apply filters
    filtered_rows = []
    for index, row in df.iterrows():
        item_name = row['Name']
        price = row['Price']
        wear = row['Wear']

        # Check if name is in filter
        if item_name in name_specific_filters:
            filter_criteria = name_specific_filters[item_name]
            max_price = filter_criteria['max_price']
            max_wear = filter_criteria['max_wear']

            if price <= max_price and wear <= max_wear:
                filtered_rows.append(row)
    
    columns = ['Name', 'Price', 'Wear', 'Suggested Price', 'Percent Difference', 'Href']
    filtered_df = pd.DataFrame(filtered_rows, columns=columns)
    
    # Nothing to send
    if filtered_df.empty:
        print("No items matched the filters.")
        return []  
    
    filtered_df = filtered_df.sort_values(by='Wear', ascending=True)

    # Nothing to send
    responses = []
    if filtered_df.empty:
        print("No items matched the filters.")
        return []  
    for index, row in filtered_df.iterrows():
        response = (
            f"----------------------------------------\n"
            f"Name:       **{row['Name']}**\n"
            f"Price  :       **${row['Price']}**\n"
            f"Float  :       **{row['Wear']}**\n"
            f"Suggested Price: **${row['Suggested Price']}** "
            f"({row['Percent Difference']:.2f}%)\n"
            f"Link: {row['Href']}\n"
            f"----------------------------------------"
            
        )
        responses.append(response)

    print(responses)
    return responses

# HTTP SERVER ------------------------------------------------------------
last_sent_messages = {}

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global last_sent_messages
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            json_data = json.loads(post_data.decode('utf-8'))
            tab_id = json_data.get('tabId')
            html_content = json_data.get('html')

            if tab_id is None or html_content is None:
                print("Invalid data received!")
                self.wfile.write(b'Invalid data')
                return

            # Save HTML locally
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, f"skinport_data_tab_{tab_id}.txt")

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(html_content)


            # Parse the HTML
            response_list = parse_html_and_create_dataframe(html_content)
            if not response_list:
                self.wfile.write(b'No matching items')
                return

            formatted_string = '\n\n'.join(response_list)

            # Deduplication
            if last_sent_messages.get(tab_id) == formatted_string:
                print(f"Duplicate message detected from Tab {tab_id}, skipping sending to Discord.")
            else:
                print(f"Sending new message to Discord from Tab {tab_id}.")
                response_channel = bot.get_channel(123)  # <------------------------------------------ Replace with your channel ID
                asyncio.run_coroutine_threadsafe(response_channel.send(formatted_string), bot.loop)
                last_sent_messages[tab_id] = formatted_string

            self.wfile.write(b'OK')

        except Exception as e:
            print("Error handling POST request:", str(e))
            self.wfile.write(b'Error')

# DISCORD BOT ---------------------------------------------------------------
tok = 'TOKEN'  # Replace with your token

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')

# Add Filter Command
@bot.command()
async def add(ctx, *, args):
    try:
        parts = args.rsplit(' ', 2)  # Splitting from the right to handle names with spaces
        if len(parts) != 3:
            await ctx.send("Usage: !add <Name> <Max Price> <Max Wear>")
            return
        
        name, max_price, max_wear = parts
        max_price = float(max_price)
        max_wear = float(max_wear)

        name_specific_filters[name] = {"max_price": max_price, "max_wear": max_wear}
        save_filters()
        await ctx.send(f"Filter added for **{name}**: Max Price = {max_price}, Max Wear = {max_wear}")
    except ValueError:
        await ctx.send("Error parsing command. Make sure price and wear are numbers.")

# Remove Filter Command
@bot.command()
async def remove(ctx, *, name: str):
    if name in name_specific_filters:
        del name_specific_filters[name]
        save_filters()
        await ctx.send(f"Filter removed for **{name}**.")
    else:
        await ctx.send(f"No filter found for **{name}**.")

# List Filters Command
@bot.command()
async def list(ctx):
    if not name_specific_filters:
        await ctx.send("No filters set.")
    else:
        msg = "**Current Filters:**\n"
        for name, vals in name_specific_filters.items():
            msg += f"- {name}: Max Price = {vals['max_price']}, Max Wear = {vals['max_wear']}\n"
        await ctx.send(msg)

# Run bot in separate thread
def run_bot():
    bot.run(tok)

bot_thread = threading.Thread(target=run_bot)
bot_thread.start()

# START SERVER ------------------------------------------------------------
server_address = ('localhost', 8000)
httpd = HTTPServer(server_address, SimpleHandler)
print("Running server on port 8000...")
httpd.serve_forever()

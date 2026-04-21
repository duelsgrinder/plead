import os
import sys
import json
import time
import requests
import websocket
from flask import Flask
from threading import Thread

# --- FLASK SERVER (For 24/7 on Render) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- BOT CONFIGURATION ---
# These are safe to leave here, but TOKEN is now a secret!
GUILD_ID = "1260440749204570294"
CHANNEL_ID = "1260440749720473695"
STATUS = "dnd" # online/dnd/idle
SELF_MUTE = True
SELF_DEAF = True

# Pull token from Render Environment Variables
TOKEN = os.getenv("TOKEN")

def check_token():
    if not TOKEN:
        print("[ERROR] TOKEN variable not found in Environment Variables!")
        sys.exit()
    
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    validate = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers=headers)
    
    if validate.status_code != 200:
        print("[ERROR] Token is invalid or expired. Update it in Render.")
        sys.exit()
    
    return validate.json()

def joiner(token, status):
    ws = websocket.WebSocket()
    try:
        ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
        start = json.loads(ws.recv())
        heartbeat = start['d']['heartbeat_interval']
        
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "Windows 10",
                    "$browser": "Google Chrome",
                    "$device": "Windows"
                },
                "presence": {"status": status, "afk": False}
            }
        }
        
        vc = {
            "op": 4,
            "d": {
                "guild_id": GUILD_ID,
                "channel_id": CHANNEL_ID,
                "self_mute": SELF_MUTE,
                "self_deaf": SELF_DEAF
            }
        }
        
        ws.send(json.dumps(auth))
        ws.send(json.dumps(vc))
        time.sleep(1) # Wait for gateway to register
        ws.send(json.dumps({"op": 1, "d": None})) # Heartbeat
        ws.close()
    except Exception as e:
        print(f"Gateway Error: {e}")

def run_bot():
    userinfo = check_token()
    
    # Fix the 'clear' vs 'cls' error
    if os.name == 'nt':
        os.system("cls")
    else:
        os.system("clear")
        
    print(f"Logged in as {userinfo['username']}#{userinfo.get('discriminator', '0')}")
    
    while True:
        try:
            joiner(TOKEN, STATUS)
        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(30)

if __name__ == "__main__":
    # Start the web server first
    keep_alive()
    # Start the bot joiner
    run_bot()
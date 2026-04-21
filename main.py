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
    # Render usually provides a port, but 8080 is the default for most setups
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    print("[INFO] Starting Flask background thread...")
    t = Thread(target=run_flask)
    t.daemon = True # This ensures the thread closes when the main program stops
    t.start()

# --- BOT CONFIGURATION ---
GUILD_ID = "1260440749204570294"
CHANNEL_ID = "1260440749720473695"
STATUS = "dnd" # online/dnd/idle
SELF_MUTE = True
SELF_DEAF = True

# Pull token from Render Environment Variables (Secrets)
TOKEN = os.getenv("TOKEN")

def check_token():
    if not TOKEN:
        print("[ERROR] TOKEN variable not found in Environment Variables!")
        print("Go to Render -> Environment -> Add 'TOKEN' with your account token.")
        sys.exit()
    
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    # Standard API check
    validate = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
    
    if validate.status_code != 200:
        print(f"[ERROR] Token is invalid. Discord returned: {validate.status_code}")
        sys.exit()
    
    return validate.json()

def joiner(token, status):
    ws = websocket.WebSocket()
    try:
        ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
        
        # Receive the Hello packet
        hello = json.loads(ws.recv())
        
        # Identify payload
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": ""
                },
                "presence": {"status": status, "afk": False}
            }
        }
        ws.send(json.dumps(auth))
        
        # Critical: Give Discord a second to authenticate before joining VC
        time.sleep(2)
        
        # Voice state update payload
        vc = {
            "op": 4,
            "d": {
                "guild_id": GUILD_ID,
                "channel_id": CHANNEL_ID,
                "self_mute": SELF_MUTE,
                "self_deaf": SELF_DEAF
            }
        }
        ws.send(json.dumps(vc))
        
        # Send heartbeat to stay connected briefly
        ws.send(json.dumps({"op": 1, "d": None}))
        
        print(f"[SUCCESS] Join request sent to channel {CHANNEL_ID}")
        ws.close()
    except Exception as e:
        print(f"[GATEWAY ERROR] {e}")

def run_bot():
    print("[INFO] Validating Token...")
    userinfo = check_token()
    
    # Clean screen logic
    if os.name == 'nt':
        os.system("cls")
    else:
        os.system("clear")
        
    print(f"--- Logged in as {userinfo['username']} ---")
    
    while True:
        try:
            joiner(TOKEN, STATUS)
        except Exception as e:
            print(f"[LOOP ERROR] {e}")
        
        # Discord usually keeps you in VC as long as the session is "fresh"
        # 30-60 seconds is a safe interval
        time.sleep(30)

if __name__ == "__main__":
    # 1. Start the web server (Pings this to keep it awake)
    keep_alive()
    
    # 2. Start the actual Discord bot process
    run_bot()

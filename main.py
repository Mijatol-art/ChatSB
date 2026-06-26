import asyncio
import aiohttp
import os
import random
import logging
import sys
import json
from conversations import SCENARIOS

# --- CẤU HÌNH LOGGING CHUYÊN NGHIỆP ---
LOG_FILE = "system_health.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("StarrySystem")

TOKENS = [t.strip() for t in os.getenv("TOKEN", "").split(",") if t.strip()]
CHANNEL_ID = os.getenv("CHANNEL_ID")
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")
OWNER_ID = "1369831885462835252"
API = "https://discord.com/api/v10"
MEMBER_NAMES = ["Kikuri", "Nijika", "PA-san", "Ryo", "Kita", "Seika", "Hitori", "TeamStarry"]

def log_critical(msg): logger.error(f"[!!! CRITICAL !!!] {msg}")
def log_safe(msg): logger.debug(f"[IGNORE] {msg}")

class BotManager:
    def __init__(self, session):
        self.session = session
        self.queue = asyncio.Queue(maxsize=10)
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.starry_token = TOKENS[-1]

    # --- HỆ THỐNG ĐIỀU KHIỂN (TEAM STARRY) ---
    async def control_hub(self):
        ws_url = "wss://gateway.discord.gg/?v=10&encoding=json"
        while True:
            try:
                async with self.session.ws_connect(ws_url) as ws:
                    await ws.send_json({"op": 2, "d": {"token": self.starry_token, "capabilities": 16381, "properties": {"os": "Linux", "browser": "Chrome", "device": "Starry Bar™"}}})
                    # Set RPC
                    await ws.send_json({"op": 3, "d": {"since": 0, "activities": [{"name": "Starry Bar™", "type": 0, "details": "Managing System", "state": "Running Live"}], "status": "online", "afk": False}})
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("t") == "MESSAGE_CREATE":
                                msg_data = data["d"]
                                if msg_data["author"]["id"] == OWNER_ID:
                                    cmd = msg_data["content"].strip().lower()
                                    if cmd == "!pause": self.pause_event.clear()
                                    elif cmd == "!resume": self.pause_event.set()
                                    elif cmd == "!logs":
                                        with open(LOG_FILE, "r") as f:
                                            crit = [l for l in f.readlines() if "[!!! CRITICAL !!!]" in l][-10:]
                                            await self.session.post(f"{API}/channels/{msg_data['channel_id']}/messages", headers={"Authorization": self.starry_token}, json={"content": f"🛡️ BÁO CÁO:\n```\n{''.join(crit)}```"})
            except Exception as e:
                log_critical(f"Gateway ngắt: {e}")
                await asyncio.sleep(10)

    # --- HỆ THỐNG VẬN HÀNH ---
    async def scenario_runner(self):
        while True:
            for scenario in SCENARIOS:
                for speaker, content in scenario:
                    await self.pause_event.wait()
                    payload = {"content": random.choice(["https://media.tenor.com/gdojpTc0GOMAAAAi/bocchi-the-rock-btr.gif"]) if random.random() < 0.25 else content}
                    await self.queue.put((speaker, payload))
                    await self.queue.join()
                    await asyncio.sleep(random.uniform(12, 18))
            await asyncio.sleep(60)

    async def bot_worker(self, name, token):
        while True:
            try:
                await self.session.patch(f"{API}/channels/{VOICE_CHANNEL_ID}/voice-states/@me", headers={"Authorization": token}, json={"channel_id": VOICE_CHANNEL_ID, "self_mute": True})
                while True:
                    await self.pause_event.wait()
                    speaker, payload = await self.queue.get()
                    if speaker == name:
                        await self.session.post(f"{API}/channels/{CHANNEL_ID}/typing", headers={"Authorization": token})
                        await asyncio.sleep(len(payload.get("content", "")) / 5 + 1.5)
                        async with self.session.post(f"{API}/channels/{CHANNEL_ID}/messages", headers={"Authorization": token}, json=payload) as resp:
                            if resp.status == 429: await asyncio.sleep(30)
                            elif resp.status >= 400: log_critical(f"Lỗi gửi từ {name}: {resp.status}")
                    self.queue.task_done()
            except Exception as e:
                log_safe(f"Lỗi mạng worker {name}: {e}")
                await asyncio.sleep(5)

async def main():
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        sys_manager = BotManager(session)
        tasks = [asyncio.create_task(sys_manager.bot_worker(MEMBER_NAMES[i], TOKENS[i])) for i in range(len(TOKENS))]
        tasks.append(asyncio.create_task(sys_manager.scenario_runner()))
        tasks.append(asyncio.create_task(sys_manager.control_hub()))
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

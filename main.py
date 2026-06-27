# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import os
import random
import logging
import sys
import json
from conversations import SCENARIOS

# --- CAU HINH ---
LOG_FILE = "system_health.log"
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("StarrySystem")

TOKENS = [t.strip() for t in os.getenv("TOKEN", "").split(",") if t.strip()]
CHANNEL_ID = os.getenv("CHANNEL_ID")
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")
OWNER_ID = "1369831885462835252"
API = "https://discord.com/api/v10"
MEMBER_NAMES = ["Kikuri", "Nijika", "PA-san", "Ryo", "Kita", "Seika", "Hitori", "TeamStarry"]

def log_critical(msg): logger.error(f"[!!! CRITICAL !!!] {msg}")
def log_safe(msg): logger.debug(f"[IGNORE] {msg}")

# --- HEALTH CHECK SERVER ---
async def health_server():
    port = int(os.getenv("PORT", 8080))
    async def handle(reader, writer):
        await reader.read(1024)
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
        await writer.drain()
        writer.close()
    server = await asyncio.start_server(handle, "0.0.0.0", port)
    logger.info(f"Health check server listening on port {port}")
    async with server:
        await server.serve_forever()

class BotManager:
    def __init__(self, session):
        self.session = session
        self.queue = asyncio.Queue(maxsize=10)
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.starry_token = TOKENS[-1]

    async def control_hub(self):
        ws_url = "wss://gateway.discord.gg/?v=10&encoding=json"
        while True:
            try:
                async with self.session.ws_connect(ws_url) as ws:
                    await ws.send_json({"op": 2, "d": {"token": self.starry_token, "capabilities": 16381, "properties": {"os": "Linux", "browser": "Chrome", "device": "Starry Bar"}}})
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
                                        report = "".join(crit)
                                        await self.session.post(
                                            f"{API}/channels/{msg_data['channel_id']}/messages",
                                            headers={"Authorization": self.starry_token},
                                            json={"content": f"BAO CAO:\n{report}"}
                                        )
            except Exception as e:
                log_critical(f"Gateway ngat: {e}")
                await asyncio.sleep(10)

    async def scenario_runner(self):
        while True:
            for scenario in SCENARIOS:
                for speaker, content in scenario:
                    await self.pause_event.wait()
                    payload = {"content": "https://media.tenor.com/gdojpTc0GOMAAAAi/bocchi-the-rock-btr.gif" if random.random() < 0.25 else content}
                    await self.queue.put((speaker, payload))
                    await asyncio.sleep(random.uniform(5, 8))
            await asyncio.sleep(60)

    async def bot_worker(self, name, token):
        try: await self.session.patch(f"{API}/channels/{VOICE_CHANNEL_ID}/voice-states/@me", headers={"Authorization": token}, json={"channel_id": VOICE_CHANNEL_ID, "self_mute": True})
        except: pass
        while True:
            try:
                await self.pause_event.wait()
                speaker, payload = await self.queue.get()
                if speaker == name:
                    await self.session.post(f"{API}/channels/{CHANNEL_ID}/typing", headers={"Authorization": token})
                    await asyncio.sleep(1.5)
                    async with self.session.post(f"{API}/channels/{CHANNEL_ID}/messages", headers={"Authorization": token}, json={"content": payload["content"]}) as resp:
                        if resp.status == 429: await asyncio.sleep(30)
                self.queue.task_done()
            except Exception as e:
                log_safe(f"Loi worker {name}: {e}")
                await asyncio.sleep(5)

async def main():
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        sys_manager = BotManager(session)
        tasks = [asyncio.create_task(sys_manager.bot_worker(MEMBER_NAMES[i], TOKENS[i])) for i in range(len(TOKENS))]
        tasks.append(asyncio.create_task(sys_manager.scenario_runner()))
        tasks.append(asyncio.create_task(sys_manager.control_hub()))
        tasks.append(asyncio.create_task(health_server()))
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

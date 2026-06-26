import asyncio
import requests
import os
import random
from conversations import SCENARIOS

# --- CẤU HÌNH ---
TOKENS = [t.strip() for t in os.getenv("TOKEN", "").split(",") if t.strip()]
CHANNEL_ID = os.getenv("CHANNEL_ID")
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")
API = "https://discord.com/api/v10"
MEMBER_NAMES = ["Kikuri", "Nijika", "PA-san", "Ryo", "Kita", "Seika", "Hitori", "TeamStarry"]

# Folder GIF nhân vật (Bocchi The Rock ONLY)
GIF_DB = {
    "Kikuri": ["https://c.tenor.com/kVcowUpmbaAAAAAd/tenor.gif"],
    "Nijika": ["https://c.tenor.com/MsRCCE3joVwAAAAd/tenor.gif"],
    "PA-san": ["https://c.tenor.com/btHsggSMhoAAAAAC/tenor.gif"],
    "Ryo": ["https://c.tenor.com/F_5MgKzJGDIAAAAC/tenor.gif"],
    "Kita": ["https://media.tenor.com/roFXXZEDobUAAAAi/kita-kita-ikuyo.gif"],
    "Seika": ["https://c.tenor.com/_y_NEEzQWewAAAAC/tenor.gif"],
    "Hitori": ["https://media.tenor.com/gdojpTc0GOMAAAAi/bocchi-the-rock-btr.gif"],
    "TeamStarry": ["https://c.tenor.com/sihR3Fv5t8AAAAAd/tenor.gif"]
}

class BotManager:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def scenario_runner(self):
        while True:
            for scenario in SCENARIOS:
                for speaker, content in scenario:
                    # 25% cơ hội gửi GIF theo nhân vật
                    if random.random() < 0.25:
                        payload = {"content": random.choice(GIF_DB.get(speaker, ["https://tenor.com/view/bocchi-the-rock-gif-26732454"]))}
                    else:
                        payload = {"content": content}
                    
                    await self.queue.put((speaker, payload))
                    await self.queue.join()
                    await asyncio.sleep(random.uniform(5, 8))
                await asyncio.sleep(60)

    async def bot_worker(self, index):
        name = MEMBER_NAMES[index]
        token = TOKENS[index]
        headers = {"Authorization": token, "Content-Type": "application/json"}
        
        # Join voice
        try:
            requests.patch(f"{API}/channels/{VOICE_CHANNEL_ID}/voice-states/@me", 
                           headers=headers, json={"channel_id": VOICE_CHANNEL_ID, "self_mute": True})
        except: pass
        
        while True:
            speaker, payload = await self.queue.get()
            if speaker == name:
                try:
                    requests.post(f"{API}/channels/{CHANNEL_ID}/typing", headers=headers)
                    await asyncio.sleep(2)
                    requests.post(f"{API}/channels/{CHANNEL_ID}/messages", headers=headers, json=payload)
                    print(f"[{name}] Done: {payload['content'][:30]}...")
                except: pass
            self.queue.task_done()

async def main():
    manager = BotManager()
    tasks = [asyncio.create_task(manager.bot_worker(i)) for i in range(8)]
    tasks.append(asyncio.create_task(manager.scenario_runner()))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

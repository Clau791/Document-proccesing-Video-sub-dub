#!/usr/bin/env python3
import requests
import json
import time

# Configurare endpoint Ollama
url = "http://86.126.134.77:11434/api/generate"

# Prompt de test
payload = {
    "model": "gemma3:27b",  # Poți schimba în mistral:Q4_K_M
    "prompt": """Tradu in romana : 天空燃烧起来。灰烬和鲜血的气息随风飘荡，飘过这座曾经骄傲的城市的残骸。惨叫声早已消散，只剩下火焰的噼啪声和远处那股势不可挡的力量有节奏的行进声。
在入侵者的铁靴下，鹅卵石路面沾满了雨水和鲜血，在镌刻在黑色钢铁上的深红色符文诡异的光芒下闪闪发光。他们悄无声息地前进，井然有序。没有战吼，没有犹豫，只有超越凡人理解的纪律。
入侵来得迅速而无情。""",
    "stream": True,
    # păstrează modelul încărcat în RAM (evită cold start la cererile următoare)
    "keep_alive": "30m",
    # poți limita output-ul (mai rapid = mai puține tokenuri)
    # "num_predict": 64,
}

print("🤖 Trimit cererea către Ollama...\n")

start_time = time.time()

try:
    with requests.post(url, json=payload, stream=True, timeout=120) as response:
        if response.status_code != 200:
            print(f"❌ Eroare: status {response.status_code}")
            print(response.text)
            exit(1)

        full_text = ""
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            # Afișează tokenurile în timp real
            if "response" in data:
                print(data["response"], end="", flush=True)
                full_text += data["response"]

            if data.get("done"):
                break

        print("\n\n---\n✅ Răspuns complet:")
        print(full_text)

except requests.exceptions.ConnectionError:
    print("❌ Conexiunea a eșuat. Asigură-te că Ollama rulează și portul 11434 este deschis.")
except requests.exceptions.Timeout:
    print("⏰ Timeout: Ollama a răspuns prea lent.")
except Exception as e:
    print(f"⚠️ Eroare neașteptată: {e}")

end_time = time.time()
duration = end_time - start_time
print(f"\n⏱️ Durata totală: {duration:.2f} secunde")

"""Async Ollama API client."""

import aiohttp

from config import DefaultConfig

CONFIG = DefaultConfig()


async def call_ollama(message: str, history: list[dict] | None = None) -> str:
    url = f"{CONFIG.OLLAMA_BASE_URL}/api/generate"

    history_text = "".join(f"{msg["role"]}: {msg["content"]}\n" for msg in (history or []))
    prompt = f"{history_text}User: {message}\nAssistant:"

    payload = {
        "model": CONFIG.OLLAMA_MODEL,
        "system": "請以簡短的方式回答問題，並且盡量使用繁體中文。",
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "(Ollama response format error)")
                return f"(Ollama returned error status: {resp.status})"
            
    except aiohttp.ClientConnectorError:
        return f"(無法連線至 Ollama，請確認服務是否在 {CONFIG.OLLAMA_BASE_URL} 執行中)"
    
    except Exception as exc:
        return f"(呼叫 Ollama 時發生例外：{exc})"

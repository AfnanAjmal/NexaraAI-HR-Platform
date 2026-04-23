import httpx

from backend.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


# -------------------
# 1. TTS
# -------------------
async def text_to_audio(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

    headers = {
        "xi-api-key"    : ELEVENLABS_API_KEY,
        "Content-Type"  : "application/json",
        "Accept"        : "audio/mpeg",
    }

    payload = {
        "text"          : text,
        "model_id"      : "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs TTS failed [{response.status_code}]: {response.text}"
        )

    return response.content

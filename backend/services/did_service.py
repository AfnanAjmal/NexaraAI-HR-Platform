"""
D-ID Lip Sync Service

IMPORTANT — LOCAL DEVELOPMENT NOTE:
D-ID requires a PUBLICLY ACCESSIBLE URL for the source photo.
http://localhost:8000 is NOT accessible from D-ID's servers.

For local dev, use ngrok:
  1. pip install pyngrok
  2. ngrok http 8000
  3. Copy the https://xxxx.ngrok.io URL
  4. Update SARAH_PHOTO_URL in .env:
       SARAH_PHOTO_URL=https://xxxx.ngrok.io/static/sarah.jpg
  5. Restart the server

For production, deploy the server and use its public URL.
"""

import asyncio

import httpx

from backend.config import DID_API_KEY


# -------------------
# 1. Auth header
# -------------------
def _auth_header() -> str:
    return f"Basic {DID_API_KEY}"


# -------------------
# 2. Lip sync
# -------------------
async def generate_lip_sync_video(text: str, photo_url: str) -> str:
    headers = {
        "Authorization": _auth_header(),
        "Content-Type" : "application/json",
    }

    payload = {
        "source_url": photo_url,
        "script"    : {
            "type"    : "text",
            "input"   : text,
            "provider": {
                "type"    : "microsoft",
                "voice_id": "en-US-JennyNeural",
            },
        },
        "config": {"fluent": True, "pad_audio": 0.0},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        create_res = await client.post(
            "https://api.d-id.com/talks",
            headers=headers,
            json=payload,
        )

    if create_res.status_code not in (200, 201):
        raise RuntimeError(
            f"D-ID create talk failed [{create_res.status_code}]: {create_res.text}"
        )

    talk_id = create_res.json().get("id")
    if not talk_id:
        raise RuntimeError("D-ID response missing talk id")

    # -------------------
    # 3. Poll for result
    # -------------------
    poll_url  = f"https://api.d-id.com/talks/{talk_id}"
    deadline  = 30
    interval  = 1.5
    elapsed   = 0.0

    async with httpx.AsyncClient(timeout=15) as client:
        while elapsed < deadline:
            await asyncio.sleep(interval)
            elapsed += interval

            poll_res  = await client.get(poll_url, headers=headers)
            poll_data = poll_res.json()
            status    = poll_data.get("status")

            if status == "done":
                result_url = poll_data.get("result_url")
                if not result_url:
                    raise RuntimeError("D-ID talk done but result_url missing")
                return result_url

            if status == "error":
                raise RuntimeError(f"D-ID talk failed: {poll_data.get('error', 'unknown')}")

    raise RuntimeError("D-ID talk timed out after 30 seconds")

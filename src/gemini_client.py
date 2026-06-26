"""Thin wrapper around the FREE Gemini API tier (used for research + script)."""
import google.generativeai as genai
from tenacity import retry, wait_exponential, stop_after_attempt
from config import SECRETS
from utils import get_logger

log = get_logger("gemini")
MODEL = "gemini-2.0-flash"  # free-tier, fast, long-context

def _model():
    if not SECRETS["GEMINI_API_KEY"]:
        raise RuntimeError("GEMINI_API_KEY missing — add it to .env / GitHub Secrets")
    genai.configure(api_key=SECRETS["GEMINI_API_KEY"])
    return genai.GenerativeModel(MODEL)

@retry(wait=wait_exponential(min=4, max=60), stop=stop_after_attempt(5))
def ask(prompt: str, temperature: float = 0.7) -> str:
    resp = _model().generate_content(
        prompt, generation_config={"temperature": temperature, "max_output_tokens": 8192}
    )
    return resp.text.strip()

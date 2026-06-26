"""Thin wrapper around the FREE Gemini API tier (research + script).
Tries several free models in order, so a per-model zero-quota or a deprecated
model name doesn't kill the whole run."""
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from tenacity import (retry, wait_exponential, stop_after_attempt,
                      retry_if_not_exception_type)
from config import SECRETS
from utils import get_logger

log = get_logger("gemini")

# Current free-tier models, tried top-to-bottom until one answers.
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-1.5-flash",
]

def _configure():
    if not SECRETS["GEMINI_API_KEY"]:
        raise RuntimeError("GEMINI_API_KEY missing — add it to .env / GitHub Secrets")
    genai.configure(api_key=SECRETS["GEMINI_API_KEY"])

# retry only on transient errors (network); quota errors skip straight to next model
@retry(wait=wait_exponential(min=5, max=40), stop=stop_after_attempt(3),
       retry=retry_if_not_exception_type(ResourceExhausted))
def _try_one(model_name, prompt, temperature):
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(
        prompt, generation_config={"temperature": temperature, "max_output_tokens": 8192})
    return resp.text.strip()

def ask(prompt: str, temperature: float = 0.7) -> str:
    _configure()
    last = None
    for m in MODELS:
        try:
            out = _try_one(m, prompt, temperature)
            log.info("used model: %s", m)
            return out
        except ResourceExhausted as e:
            log.warning("model %s: quota 0/exhausted -> trying next", m); last = e
        except Exception as e:
            log.warning("model %s failed (%s) -> trying next", str(m), str(e)[:120]); last = e
    raise RuntimeError(
        "Saare free Gemini models fail ho gaye. Sabse aam wajah: free quota wali "
        "nayi key chahiye (naye project me banao). Last error: %s" % last)

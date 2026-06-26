"""Gather facts for the chosen topic (Wikipedia + Gemini synthesis)."""
import wikipediaapi
from utils import get_logger
import gemini_client

log = get_logger("research")

def research(topic: dict) -> dict:
    title = topic["title"]
    log.info("Researching: %s", title)

    # 1) pull factual base from Wikipedia (free, citable)
    wiki = wikipediaapi.Wikipedia(user_agent="ItihaasBot/0.1", language="en")
    facts = ""
    for q in [title, topic.get("region", "")]:
        page = wiki.page(q)
        if page.exists():
            facts += page.summary[:3000] + "\n\n"

    # 2) ask Gemini to verify + build a fact sheet with a timeline + the 'why'
    prompt = (
        f"Topic: {title}\nKnown facts:\n{facts[:6000]}\n\n"
        "Ek detailed, factually-accurate research brief banao (Hindi me) jisme ho: "
        "(1) timeline of events, (2) key people, (3) the REAL reasons behind the event, "
        "(4) lesser-known true details, (5) 8-12 visual scene keywords (English, comma-separated) "
        "for image/video search. Headings ke saath structured text do."
    )
    brief = gemini_client.ask(prompt, temperature=0.4)
    return {"title": title, "wiki_facts": facts, "brief": brief}

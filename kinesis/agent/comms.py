"""Communication agent: given what someone just said, propose four replies the
person might want to say. Keeps a short memory of the conversation so replies
stay on topic. Gemini when available, sensible fallbacks when not."""
from collections import deque

from kinesis.agent import llm

QUESTION_WORDS = ("do ", "does ", "did ", "are ", "is ", "can ", "could ", "would ", "will ", "should ", "have ", "want ")


def _fallback(heard):
    h = heard.strip().lower()
    if h.startswith(QUESTION_WORDS):
        return ["Yes", "No", "Maybe later", "Can you ask me another way?"]
    if h.startswith(("how are", "how do you feel", "how did you")):
        return ["Pretty good", "Not great today", "Tired", "Can we talk later?"]
    if "?" in h:
        return ["I'm not sure", "Give me a minute", "Can you say that again?", "Let's talk about it later"]
    return ["Okay", "Thank you", "Tell me more", "I need a minute"]


class CommunicationAgent:
    def __init__(self, profile):
        self.profile = profile
        self.history = deque(maxlen=12)

    def heard(self, speaker, text):
        self.history.append(f"{speaker}: {text}")

    def said(self, text):
        self.history.append(f"{self.profile['name']}: {text}")

    def replies(self, speaker, text, setting="home"):
        self.heard(speaker, text)
        p = self.profile
        prompt = (
            f"You help {p['name']} reply in conversation. {p['name']} cannot speak or move and picks a reply "
            f"with a brain-computer interface, so each reply must be short. About {p['name']}: {p['about']}. "
            f"Setting: {setting}.\nRecent conversation:\n" + "\n".join(self.history) +
            f"\n\nWrite exactly 4 replies {p['name']} might want to say next to {speaker}, first person, "
            "under 9 words each, covering different intents (agree, decline or disagree, ask something back, "
            "a feeling or a need). Never invent medical facts. Return only a JSON array of 4 strings."
        )
        out = llm.ask_json(prompt)
        if isinstance(out, list) and len(out) >= 4 and all(isinstance(x, str) for x in out[:4]):
            return out[:4], "gemini"
        return _fallback(text), "fallback"

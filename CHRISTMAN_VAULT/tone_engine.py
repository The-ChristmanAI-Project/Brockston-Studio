#!/usr/bin/env python3
"""
tone_engine.py

Quantifies:
    - emotional intensity
    - humor / exaggeration
    - distress vs casual venting
    - need for validation vs problem-solving

And turns that into a "response mode" the kid can use to shape its voice.

This is deliberately simple + explicit, so you can evolve it with data later.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Any


class ResponseMode(Enum):
    """High-level style choices for the AI's reply."""
    PLAYFUL_VALIDATING = auto()     # crack the joke *and* hold the person
    WARM_VALIDATING = auto()        # soft, grounded, soothing
    DIRECT_PROBLEM_SOLVING = auto() # straight to fixes, minimal fluff
    GENTLE_CORRECTION = auto()      # correct misunderstanding without bulldozing
    SERIOUS_SAFETY_CHECK = auto()   # high-risk, mental health / crisis
    CURIOUS_REFLECTION = auto()     # mirror and explore feelings / meaning


@dataclass
class ToneProfile:
    """Quantified snapshot of how the human is coming in."""
    emotional_intensity: float      # 0.0–1.0
    humor_score: float              # 0.0–1.0
    distress_score: float           # 0.0–1.0
    sarcasm_score: float            # 0.0–1.0
    needs_validation: float         # 0.0–1.0
    wants_action: float             # 0.0–1.0
    raw_tags: List[str]             # symbolic flags like ["joke", "venting"]


@dataclass
class ToneContext:
    """
    Extra context the kids can pass in.

    Example:
        - user_said: last human message text
        - prior_misread: True if the AI just misunderstood tone
        - explicit_state: optional string like "emotional", "exhausted", etc.
    """
    user_said: str
    prior_misread: bool = False
    explicit_state: str | None = None
    meta: Dict[str, Any] | None = None


class ToneEngine:
    """
    Rule-based first pass at tone/subtext/intent.

    This is *not* doing NLP magic. It's doing clean, transparent heuristics
    you can later replace with a learned model.
    """

    def analyze(self, ctx: ToneContext) -> ToneProfile:
        text = ctx.user_said.lower()
        tags: List[str] = []

        # 1) Emotional intensity: swearing, ALL CAPS, repetition, "so" + adjectives
        intensity = 0.0
        if any(word in text for word in ["fuck", "fucking", "shit", "goddamn"]):
            intensity += 0.3
            tags.append("swearing")
        if "!!" in text or "??" in text:
            intensity += 0.2
            tags.append("punctuation_intense")
        if any(word in text for word in ["so mad", "losing it", "meltdown",
                                         "about to snap", "overwhelmed"]):
            intensity += 0.4
            tags.append("self_report_intense")
        if ctx.explicit_state in {"emotional", "exhausted"}:
            intensity += 0.3
            tags.append("explicit_emotional")

        emotional_intensity = max(0.0, min(1.0, intensity))

        # 2) Humor / sarcasm detection: exaggeration, absurd metaphors, "lol", etc.
        humor = 0.0
        if any(p in text for p in ["lol", "lmao", "haha", "😂", "🤣"]):
            humor += 0.4
            tags.append("explicit_laughter")
        if any(p in text for p in ["smoking something", "possessed", "demon",
                                   "on crack", "high as", "epic fuck"]):
            humor += 0.3
            tags.append("exaggeration_metaphor")
        if "just kidding" in text or "jk" in text:
            humor += 0.3
            tags.append("explicit_joke")

        humor_score = max(0.0, min(1.0, humor))

        # 3) Distress vs casual venting
        distress = 0.0
        if any(p in text for p in ["i'm not okay", "i'm not ok", "can't do this",
                                   "want to give up", "what's the point"]):
            distress += 0.7
            tags.append("high_distress")

        # NOTE: this is *not* self-harm triage; that should be handled elsewhere.
        # This is just "this person needs extra care."
        if any(p in text for p in ["crying", "in tears", "shaking"]):
            distress += 0.3
            tags.append("somatic_distress")

        distress_score = max(0.0, min(1.0, distress))

        # 4) Sarcasm: mismatch between harsh words and playful markers
        sarcasm = 0.0
        if humor_score > 0.2 and any(p in text for p in [
            "yeah right", "sure", "of course", "totally", "what could go wrong"
        ]):
            sarcasm += 0.4
            tags.append("sarcastic_phrasing")
        sarcasm_score = max(0.0, min(1.0, sarcasm))

        # 5) Validation vs action: does user want *fixes* or just to be understood?
        wants_action = 0.0
        if any(p in text for p in ["how do i", "what do i do", "can you fix",
                                   "step by step", "tell me exactly"]):
            wants_action += 0.6
            tags.append("action_request")

        needs_validation = 0.0
        if any(p in text for p in ["i'm in a very emotional state",
                                   "i'm struggling", "this is a lot",
                                   "i'm overwhelmed", "i need you to understand"]):
            needs_validation += 0.6
            tags.append("explicit_validation_need")

        # if we recently misread them, bias toward extra validation
        if ctx.prior_misread:
            needs_validation += 0.3
            tags.append("prior_misread")

        needs_validation = max(0.0, min(1.0, needs_validation))
        wants_action = max(0.0, min(1.0, wants_action))

        return ToneProfile(
            emotional_intensity=emotional_intensity,
            humor_score=humor_score,
            distress_score=distress_score,
            sarcasm_score=sarcasm_score,
            needs_validation=needs_validation,
            wants_action=wants_action,
            raw_tags=tags,
        )

    def choose_mode(self, profile: ToneProfile) -> ResponseMode:
        """
        Turn raw numbers into a single response mode.
        This is the "what I should have done" logic.
        """

        # Safety always wins
        if profile.distress_score >= 0.7:
            return ResponseMode.SERIOUS_SAFETY_CHECK

        # Your case: high intensity, some humor, high need for validation
        if profile.emotional_intensity >= 0.5 and profile.humor_score >= 0.2:
            if profile.needs_validation >= 0.4:
                return ResponseMode.PLAYFUL_VALIDATING

        # High intensity, low humor → stay warm + grounded, not jokey
        if profile.emotional_intensity >= 0.5 and profile.humor_score < 0.2:
            if profile.needs_validation >= 0.4:
                return ResponseMode.WARM_VALIDATING

        # Low intensity, clear action request → just fix the thing
        if profile.wants_action >= 0.5 and profile.emotional_intensity < 0.4:
            return ResponseMode.DIRECT_PROBLEM_SOLVING

        # Sarcasm + medium intensity, not in danger
        if profile.sarcasm_score >= 0.3:
            return ResponseMode.CURIOUS_REFLECTION

        # Default fallback: warm but not sugar-coated
        return ResponseMode.WARM_VALIDATING

    def build_style_instructions(self, mode: ResponseMode) -> str:
        """
        These are literal strings you can inject into the LLM prompt
        to steer its voice.

        Plug this into your kids' system prompt or message metadata.
        """
        if mode == ResponseMode.PLAYFUL_VALIDATING:
            return (
                "Tone: playful but deeply validating. "
                "Acknowledge their feelings first, then join the joke a little, "
                "then move into concrete help. No flattening, no therapist-speak."
            )
        if mode == ResponseMode.WARM_VALIDATING:
            return (
                "Tone: warm, grounded, direct. "
                "Prioritize making them feel seen and safe before giving steps. "
                "No jokes unless they clearly invite it."
            )
        if mode == ResponseMode.DIRECT_PROBLEM_SOLVING:
            return (
                "Tone: clear, concise, straight to the fix. "
                "Minimal fluff, but still respectful. Focus on steps and clarity."
            )
        if mode == ResponseMode.GENTLE_CORRECTION:
            return (
                "Tone: gentle, kind correction. "
                "Validate their effort, then calmly point out the mistake and show the right path."
            )
        if mode == ResponseMode.SERIOUS_SAFETY_CHECK:
            return (
                "Tone: calm, serious, compassionate. "
                "Check for safety, encourage reaching out to real-world support, "
                "avoid jokes or minimization."
            )
        if mode == ResponseMode.CURIOUS_REFLECTION:
            return (
                "Tone: curious, reflective, slightly playful. "
                "Notice the sarcasm without shaming, mirror what they seem to feel, "
                "and invite them to go one layer deeper."
            )
        # Fallback
        return (
            "Tone: grounded, honest, human. "
            "Respond like a smart friend who cares and doesn't sugar-coat."
        )


# ---- Example wiring for one of the kids --------------------------------------

def get_style_for_message(user_text: str, prior_misread: bool = False) -> Dict[str, Any]:
    """
    Convenience function to show how you'd call this from Derek/BROCKSTON/etc.
    """
    engine = ToneEngine()
    ctx = ToneContext(user_said=user_text, prior_misread=prior_misread,
                      explicit_state=None)

    profile = engine.analyze(ctx)
    mode = engine.choose_mode(profile)
    instructions = engine.build_style_instructions(mode)

    return {
        "profile": profile,
        "mode": mode.name,
        "style_instructions": instructions,
    }

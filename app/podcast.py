from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from gtts import gTTS
from jinja2 import Template

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "vendor" / "open-notebook" / "prompts" / "podcast"
OUTPUT_DIR = REPO_ROOT / "output"


@dataclass
class PodcastResult:
    audio_path: Path
    script: str
    outline: list[str]
    briefing: str


def load_prompt_template(name: str) -> str:
    template_path = PROMPTS_DIR / name
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    fallback_templates = {
        "outline.jinja": (
            "Outline request\n"
            "Briefing:\n{{ briefing }}\n\n"
            "Context:\n{{ context }}\n"
        ),
        "transcript.jinja": (
            "Transcript request\n"
            "Briefing:\n{{ briefing }}\n\n"
            "Context:\n{{ context }}\n\n"
            "Outline:\n{{ outline }}\n"
        ),
    }
    if name in fallback_templates:
        return fallback_templates[name]
    raise FileNotFoundError(
        f"Prompt template '{name}' not found at {template_path} "
        "and no fallback is available."
    )


def render_prompt(template_text: str, **context: object) -> str:
    return Template(template_text).render(**context)


def detect_language(text: str) -> str:
    if re.search(r"[А-Яа-я]", text):
        return "ru"
    return "en"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def extract_outline(sentences: Iterable[str], max_items: int = 5) -> list[str]:
    selected = []
    for sentence in sentences:
        if len(selected) >= max_items:
            break
        if len(sentence) > 20:
            selected.append(sentence)
    if not selected:
        selected = ["Основные идеи из предоставленного текста."]
    return selected


def build_script(topic: str, outline: list[str], language: str) -> str:
    host = "Ведущий" if language == "ru" else "Host"
    guest = "Гость" if language == "ru" else "Guest"
    intro = (
        f"{host}: Сегодня обсуждаем тему: {topic}. "
        f"Мы выделили {len(outline)} ключевых пункта."
    )
    lines = [intro]
    for idx, item in enumerate(outline, start=1):
        lines.append(f"{guest}: Пункт {idx}: {item}")
        lines.append(
            f"{host}: Интересно. Можем добавить контекст и пример для слушателей?"
        )
        lines.append(
            f"{guest}: Да, это помогает понять, как пункт {idx} влияет на практику."
        )
    lines.append(f"{host}: Спасибо за обсуждение! Подведём итог.")
    return "\n".join(lines)


def build_briefing(topic: str, outline: list[str]) -> str:
    return (
        "План выпуска:\n"
        + "\n".join(f"- {item}" for item in outline)
        + f"\nТема: {topic}"
    )


def generate_podcast(text: str) -> PodcastResult:
    sentences = split_sentences(text)
    outline = extract_outline(sentences)
    topic = sentences[0] if sentences else "Обсуждение темы"
    language = detect_language(text)

    transcript_template = load_prompt_template("transcript.jinja")
    outline_template = load_prompt_template("outline.jinja")

    briefing = build_briefing(topic, outline)
    rendered_outline_prompt = render_prompt(
        outline_template,
        briefing=briefing,
        context=text,
    )
    rendered_transcript_prompt = render_prompt(
        transcript_template,
        briefing=briefing,
        context=text,
        speakers=[
            {"name": "Host", "backstory": "Podcast host", "personality": "Warm"},
            {
                "name": "Guest",
                "backstory": "Subject matter expert",
                "personality": "Analytical",
            },
        ],
        outline="\n".join(outline),
        transcript=None,
        is_final=True,
        segment="Full episode",
        speaker_names=["Host", "Guest"],
        turns=6,
        format_instructions="JSON with transcript array",
    )

    prompt_context = "\n\n".join(
        [
            "[Open-Notebook Outline Prompt]",
            rendered_outline_prompt,
            "[Open-Notebook Transcript Prompt]",
            rendered_transcript_prompt,
        ]
    )

    script = build_script(topic, outline, language)
    script_with_notes = f"{script}\n\n{prompt_context}"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = OUTPUT_DIR / "podcast.mp3"
    tts = gTTS(script, lang=language)
    tts.save(str(audio_path))

    return PodcastResult(
        audio_path=audio_path,
        script=script_with_notes,
        outline=outline,
        briefing=briefing,
    )

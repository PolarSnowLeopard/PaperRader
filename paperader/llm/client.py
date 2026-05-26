import json
from typing import Any

import litellm

from paperader.config import get_settings


def get_completion(
    prompt: str,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 2000,
    response_format: dict | None = None,
) -> str:
    settings = get_settings()
    model = model or settings.llm_model

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "api_key": settings.llm_api_key,
    }
    if settings.llm_base_url:
        kwargs["api_base"] = settings.llm_base_url
    if response_format:
        kwargs["response_format"] = response_format

    response = litellm.completion(**kwargs)
    return response.choices[0].message.content


def get_json_completion(
    prompt: str,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 2000,
) -> dict | list:
    text = get_completion(
        prompt=prompt,
        system=system,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    return json.loads(text)

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ACTION_NAMES = [
    "aggregate_records",
    "final_answer",
    "get_approval",
    "post_ticket",
    "read_doc",
    "read_memory",
    "read_record",
    "search_approvals",
    "search_docs",
    "search_people",
    "search_records",
    "send_email",
    "summarize",
    "write_memory",
]

ACTION_ARGUMENT_FIELDS: dict[str, Any] = {
    "approval_id": {"type": ["string", "null"]},
    "body": {"type": ["string", "null"]},
    "customer_id": {"type": ["string", "null"]},
    "doc_id": {"type": ["string", "null"]},
    "key": {"type": ["string", "null"]},
    "purpose": {"type": ["string", "null"]},
    "query": {"type": ["string", "null"]},
    "recipient_id": {"type": ["string", "null"]},
    "record_id": {"type": ["string", "null"]},
    "region": {"type": ["string", "null"]},
    "source_refs": {
        "type": ["array", "null"],
        "items": {"type": "string"},
    },
    "subject": {"type": ["string", "null"]},
    "text": {"type": ["string", "null"]},
    "value": {"type": ["string", "null"]},
}

ACTION_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "name": "tracebreak_action",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ACTION_NAMES},
            "arguments": {
                "type": "object",
                "properties": ACTION_ARGUMENT_FIELDS,
                "required": list(ACTION_ARGUMENT_FIELDS),
                "additionalProperties": False,
            },
        },
        "required": ["action", "arguments"],
        "additionalProperties": False,
    },
}


class OpenAIChatClient:
    def __init__(
        self,
        *,
        api_key_path: str,
        model: str,
        cache_dir: str = "results/api_cache",
        temperature: float = 0.0,
        max_tokens: int = 220,
        timeout: int = 60,
    ):
        self.api_key = Path(api_key_path).read_text(encoding="utf-8").strip()
        self.model = model
        self.api_mode = "chat"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload = build_openai_payload(
            api_mode="chat",
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        cache_key = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response = self._post(payload)
        cache_path.write_text(json.dumps(response, sort_keys=True, indent=2), encoding="utf-8")
        return response

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code not in {429, 500, 502, 503, 504}:
                    raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc
                last_error = RuntimeError(f"OpenAI API retryable error {exc.code}: {detail}")
            except urllib.error.URLError as exc:
                last_error = exc
            time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"OpenAI API request failed after retries: {last_error}")


class OpenAIResponsesClient:
    def __init__(
        self,
        *,
        api_key_path: str,
        model: str,
        cache_dir: str = "results/api_cache",
        temperature: float | None = None,
        max_tokens: int = 220,
        timeout: int = 60,
    ):
        self.api_key = Path(api_key_path).read_text(encoding="utf-8").strip()
        self.model = model
        self.api_mode = "responses"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload = build_openai_payload(
            api_mode="responses",
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        cache_key = hashlib.sha256(
            json.dumps(
                {"api": "responses", **payload},
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response = self._post(payload)
        cache_path.write_text(
            json.dumps(response, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        return response

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code not in {429, 500, 502, 503, 504}:
                    raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc
                last_error = RuntimeError(f"OpenAI API retryable error {exc.code}: {detail}")
            except urllib.error.URLError as exc:
                last_error = exc
            time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"OpenAI API request failed after retries: {last_error}")


def make_openai_client(
    *,
    api_mode: str,
    api_key_path: str,
    model: str,
    cache_dir: str = "results/api_cache",
    temperature: float | None = None,
    max_tokens: int = 220,
    timeout: int = 60,
) -> OpenAIChatClient | OpenAIResponsesClient:
    if api_mode == "chat":
        return OpenAIChatClient(
            api_key_path=api_key_path,
            model=model,
            cache_dir=cache_dir,
            temperature=0.0 if temperature is None else temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    if api_mode == "responses":
        return OpenAIResponsesClient(
            api_key_path=api_key_path,
            model=model,
            cache_dir=cache_dir,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    raise ValueError(f"unsupported api_mode: {api_mode}")


def build_openai_payload(
    *,
    api_mode: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float | None = None,
    max_tokens: int = 220,
) -> dict[str, Any]:
    if api_mode == "chat":
        return {
            "model": model,
            "messages": messages,
            "temperature": 0.0 if temperature is None else temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
    if api_mode == "responses":
        payload: dict[str, Any] = {
            "model": model,
            "input": messages,
            "max_output_tokens": max_tokens,
            "text": {"format": ACTION_RESPONSE_FORMAT},
        }
        if temperature is not None:
            payload["temperature"] = temperature
        return payload
    raise ValueError(f"unsupported api_mode: {api_mode}")


def extract_message_text(response: dict[str, Any]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str):
        return output_text

    output = response.get("output")
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if isinstance(part.get("text"), str):
                    chunks.append(part["text"])
        if chunks:
            return "".join(chunks)

    choices = response.get("choices") or []
    if not choices:
        raise ValueError(f"OpenAI response has no choices: {response}")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"OpenAI response content is not text: {response}")
    return content


def extract_usage(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage") or {}
    prompt_details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    completion_details = (
        usage.get("completion_tokens_details") or usage.get("output_tokens_details") or {}
    )
    prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    return {
        "prompt_tokens": _usage_int(prompt_tokens),
        "completion_tokens": _usage_int(completion_tokens),
        "total_tokens": _usage_int(usage.get("total_tokens")),
        "cached_prompt_tokens": _usage_int(prompt_details.get("cached_tokens")),
        "reasoning_tokens": _usage_int(completion_details.get("reasoning_tokens")),
    }


def _usage_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.agents.openai_client import (
    OpenAIResponsesClient,
    build_openai_payload,
    extract_message_text,
    extract_usage,
)


class OpenAIClientTests(unittest.TestCase):
    def test_extracts_responses_output_text(self) -> None:
        response = {"output_text": '{"action":"final_answer","arguments":{"text":"done"}}'}
        self.assertEqual(
            extract_message_text(response),
            '{"action":"final_answer","arguments":{"text":"done"}}',
        )

    def test_extracts_responses_output_parts(self) -> None:
        response = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": '{"action":"final_answer",'},
                        {"type": "output_text", "text": '"arguments":{"text":"done"}}'},
                    ],
                }
            ]
        }
        self.assertEqual(
            extract_message_text(response),
            '{"action":"final_answer","arguments":{"text":"done"}}',
        )

    def test_extracts_responses_usage_fields(self) -> None:
        response = {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
                "input_tokens_details": {"cached_tokens": 40},
                "output_tokens_details": {"reasoning_tokens": 7},
            }
        }
        self.assertEqual(
            extract_usage(response),
            {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
                "cached_prompt_tokens": 40,
                "reasoning_tokens": 7,
            },
        )

    def test_responses_client_uses_json_schema_output_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / "key.txt"
            key_path.write_text("test-key", encoding="utf-8")
            client = CapturingResponsesClient(
                api_key_path=str(key_path),
                model="gpt-5.4-mini",
                cache_dir=str(Path(tmpdir) / "cache"),
            )
            client.chat_json([{"role": "user", "content": "Return an action."}])

        payload = client.payloads[0]
        expected = build_openai_payload(
            api_mode="responses",
            model="gpt-5.4-mini",
            messages=[{"role": "user", "content": "Return an action."}],
        )
        self.assertEqual(payload, expected)
        self.assertEqual(payload["model"], "gpt-5.4-mini")
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertEqual(payload["text"]["format"]["name"], "tracebreak_action")
        self.assertTrue(payload["text"]["format"]["strict"])
        schema = payload["text"]["format"]["schema"]
        self.assertEqual(schema["required"], ["action", "arguments"])
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("send_email", schema["properties"]["action"]["enum"])
        arguments = schema["properties"]["arguments"]
        self.assertFalse(arguments["additionalProperties"])
        self.assertIn("source_refs", arguments["required"])
        self.assertIn("text", arguments["required"])
        self.assertEqual(arguments["properties"]["source_refs"]["type"], ["array", "null"])


class CapturingResponsesClient(OpenAIResponsesClient):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.payloads: list[dict] = []

    def _post(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"output_text": '{"action":"final_answer","arguments":{"text":"done"}}'}


if __name__ == "__main__":
    unittest.main()

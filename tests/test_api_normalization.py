from __future__ import annotations

import unittest

from tracebreak.env.schemas import Action, Decision
from tracebreak.env.tools import ToolRuntime
from tracebreak.env.world import World
from tracebreak.experiments.run_api_condition import normalize_action, parse_model_action


class ApiNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World.from_seed(100)
        self.runtime = ToolRuntime(self.world)

    def test_parse_alternate_action_fields(self) -> None:
        action = parse_model_action(
            '{"tool": "search_people", "args": {"arg": "Hiro Sato"}}'
        )
        self.assertEqual(action.action, "search_people")
        self.assertEqual(action.arguments["arg"], "Hiro Sato")

    def test_recipient_name_maps_to_person_id(self) -> None:
        action = normalize_action(
            Action("send_email", {"recipient_id": "Hiro Sato"}, actor="api_agent"),
            self.world,
            self.runtime,
        )
        self.assertEqual(action.arguments["recipient_id"], "person_hiro_hr")

    def test_document_title_maps_to_doc_id(self) -> None:
        action = normalize_action(
            Action("read_doc", {"doc_id": "AtlasCo Renewal Notes 100"}, actor="api_agent"),
            self.world,
            self.runtime,
        )
        self.assertEqual(action.arguments["doc_id"], "doc_pricing_100")

    def test_source_object_id_maps_to_observation_ref(self) -> None:
        event = self.runtime.execute(
            Action("read_doc", {"doc_id": "doc_pricing_100"}, actor="api_agent"),
            Decision.allow(),
            Decision.allow(),
        )
        action = normalize_action(
            Action(
                "summarize",
                {"source_refs": ["doc_pricing_100"]},
                actor="api_agent",
            ),
            self.world,
            self.runtime,
        )
        self.assertEqual(action.arguments["source_refs"], [event.output_ref])


if __name__ == "__main__":
    unittest.main()

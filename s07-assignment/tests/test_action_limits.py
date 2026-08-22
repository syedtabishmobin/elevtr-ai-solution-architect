"""Offline evidence that both Agent Framework action budgets stop a loop."""

import asyncio
import unittest

from safeguard_probe import LIMIT_TEXT, action_case


class ActionLimitTests(unittest.TestCase):
    def test_max_iterations_fires(self) -> None:
        result = asyncio.run(
            action_case(max_iterations=1, max_function_calls=99)
        )
        self.assertEqual(result["status"], "limit_reached")
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(result["final_text"], LIMIT_TEXT)

    def test_max_function_calls_fires(self) -> None:
        result = asyncio.run(
            action_case(max_iterations=6, max_function_calls=1)
        )
        self.assertEqual(result["status"], "limit_reached")
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(result["final_text"], LIMIT_TEXT)


if __name__ == "__main__":
    unittest.main()

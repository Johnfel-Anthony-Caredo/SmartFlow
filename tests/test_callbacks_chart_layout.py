import unittest
from pathlib import Path


CALLBACKS_PATH = Path("callbacks.py")


class TestCallbacksChartLayout(unittest.TestCase):
    def test_yaxis_uses_nested_title_object_for_plotly_compatibility(self):
        text = CALLBACKS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("titlefont=", text)
        self.assertIn("title=dict(text=yaxis_title, font=dict(size=10, color='#64748b'))", text)


if __name__ == "__main__":
    unittest.main()

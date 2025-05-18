import importlib
import sys

sys.path.insert(0, "llm-training-platform/src")


def test_routes_importable():
    module = importlib.import_module("admin_dashboard.api.routes")
    assert hasattr(module, "router")

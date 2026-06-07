"""Tests for the Layer 1 builder server's security gates (templates/layer1/...).

The server is a placeholder-free .tmpl (valid Python). We load it as a module and
exercise the pure auth/host helpers + the single-flight lock without binding a
socket or invoking claude.
"""
import importlib.machinery
import importlib.util
import os
import unittest
from pathlib import Path

SERVER = (Path(__file__).resolve().parent.parent / "templates" / "layer1" /
          "builder" / "server.py.tmpl")


def load_server(token="test-token-123"):
    os.environ["BUILDER_TOKEN"] = token
    loader = importlib.machinery.SourceFileLoader("builder_server", str(SERVER))
    spec = importlib.util.spec_from_loader("builder_server", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class TokenAuthTest(unittest.TestCase):
    def test_correct_token_accepted(self):
        m = load_server("s3cret-token")
        self.assertTrue(m.token_ok("s3cret-token"))

    def test_wrong_or_missing_token_rejected(self):
        m = load_server("s3cret-token")
        self.assertFalse(m.token_ok("nope"))
        self.assertFalse(m.token_ok(""))
        self.assertFalse(m.token_ok(None))


class HostCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load_server()

    def test_loopback_allowed(self):
        for h in ("127.0.0.1:8080", "localhost:8080", "127.0.0.1",
                  "localhost", "[::1]:8080"):
            self.assertTrue(self.m.host_ok(h), h)

    def test_external_host_rejected(self):
        for h in ("evil.example.com", "evil.example.com:8080",
                  "169.254.169.254", "10.0.0.5:8080", "", None):
            self.assertFalse(self.m.host_ok(h), repr(h))


class SingleFlightTest(unittest.TestCase):
    def test_lock_is_single_flight(self):
        m = load_server()
        self.assertTrue(m._BUILD_LOCK.acquire(blocking=False))
        try:
            # a second concurrent request cannot acquire — it would get 409
            self.assertFalse(m._BUILD_LOCK.acquire(blocking=False))
        finally:
            m._BUILD_LOCK.release()
        # released again — next request proceeds
        self.assertTrue(m._BUILD_LOCK.acquire(blocking=False))
        m._BUILD_LOCK.release()


if __name__ == "__main__":
    unittest.main()

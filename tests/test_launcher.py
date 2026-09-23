import unittest

from portal.launcher import launcher_response


class LauncherOutputTests(unittest.TestCase):
    def test_account_label_cannot_inject_same_origin_script(self):
        response = launcher_response("A<script>@example.com", can_chat=True)
        markup = response.body.decode()
        self.assertIn("A&lt;script&gt;@example.com", markup)
        self.assertNotIn("<script>", markup)
        self.assertIn("default-src 'none'", response.headers["content-security-policy"])


if __name__ == "__main__":
    unittest.main()

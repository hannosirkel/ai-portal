import unittest

from portal.auth import Principal, classify_path, permitted


class PortalAuthorizationTests(unittest.TestCase):
    def test_launcher_requires_authenticated_principal(self):
        self.assertFalse(permitted(None, "/"))
        self.assertTrue(permitted(Principal("person-1", frozenset()), "/"))

    def test_chat_requires_explicit_portal_group(self):
        restricted = Principal("person-1", frozenset())
        user = Principal("person-2", frozenset({"ai-portal-user"}))
        admin = Principal("person-3", frozenset({"ai-portal-admin"}))
        self.assertFalse(permitted(restricted, "/chat"))
        self.assertFalse(permitted(restricted, "/chat/api/messages"))
        self.assertTrue(permitted(user, "/chat/api/messages"))
        self.assertTrue(permitted(admin, "/chat/api/messages"))

    def test_scratch_is_reserved_and_denied_until_hub_exists(self):
        admin = Principal("person-3", frozenset({"ai-portal-admin"}))
        self.assertEqual(classify_path("/scratch/editor"), "scratch")
        self.assertFalse(permitted(admin, "/scratch/editor"))

    def test_prefix_matching_does_not_accept_nearby_paths(self):
        user = Principal("person-2", frozenset({"ai-portal-user"}))
        self.assertEqual(classify_path("/chatty"), "unknown")
        self.assertFalse(permitted(user, "/chatty"))
        self.assertFalse(permitted(user, "//chat"))
        self.assertFalse(permitted(user, "/chat/../admin"))

    def test_unrelated_authentik_group_does_not_grant_chat(self):
        principal = Principal("person-1", frozenset({"platform-administrators"}))
        self.assertFalse(permitted(principal, "/chat"))


if __name__ == "__main__":
    unittest.main()

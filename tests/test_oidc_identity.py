import unittest

from portal.access import AccessIdentity
from portal.oidc import OIDCRejected, PortalSession, session_from_claims


class OIDCIdentityTests(unittest.TestCase):
    def setUp(self):
        self.access = AccessIdentity(
            subject="access-person-1", email="person@example.com"
        )

    def test_verified_claims_bind_to_access_email(self):
        session = session_from_claims(
            {
                "sub": "authentik-person-1",
                "email": "Person@Example.com",
                "groups": ["ai-portal-user", "unrelated"],
            },
            self.access,
        )
        self.assertEqual(session.oidc_subject, "authentik-person-1")
        self.assertEqual(
            session.principal().groups, frozenset({"ai-portal-user", "unrelated"})
        )
        self.assertEqual(session.principal_for(self.access), session.principal())

    def test_oidc_and_access_emails_must_match(self):
        with self.assertRaises(OIDCRejected):
            session_from_claims(
                {
                    "sub": "authentik-person-2",
                    "email": "other@example.com",
                    "groups": ["ai-portal-admin"],
                },
                self.access,
            )

    def test_session_is_bound_to_current_access_identity(self):
        session = PortalSession(
            "authentik-person-1",
            "access-person-1",
            "person@example.com",
            frozenset({"ai-portal-user"}),
        )
        other = AccessIdentity("access-person-2", "other@example.com")
        self.assertIsNone(session.principal_for(other))
        self.assertIsNotNone(session.principal_for(self.access))
        same_email_other_subject = AccessIdentity(
            "access-person-2", "person@example.com"
        )
        self.assertIsNone(session.principal_for(same_email_other_subject))

    def test_missing_or_malformed_groups_fail_closed(self):
        for groups in (None, "ai-portal-admin", ["ai-portal-admin", 42]):
            with self.subTest(groups=groups), self.assertRaises(OIDCRejected):
                session_from_claims(
                    {
                        "sub": "authentik-person-1",
                        "email": "person@example.com",
                        "groups": groups,
                    },
                    self.access,
                )

    def test_subject_and_email_are_required(self):
        for claims in (
            {"sub": "", "email": "person@example.com", "groups": []},
            {"sub": "authentik-person-1", "email": "", "groups": []},
        ):
            with self.subTest(claims=claims), self.assertRaises(OIDCRejected):
                session_from_claims(claims, self.access)


if __name__ == "__main__":
    unittest.main()

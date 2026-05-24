import unittest

from pages import admin_roles


class TestAdminRolesHelpers(unittest.TestCase):
    def test_permission_key(self):
        self.assertEqual(
            admin_roles.permission_key("dashboard", "view"),
            "dashboard:view",
        )

    def test_flatten_permission_groups(self):
        flat = admin_roles.flatten_permission_groups(admin_roles.PERMISSION_GROUPS)
        self.assertGreater(len(flat), 0)
        self.assertEqual(flat[0][0], "dashboard")

    def test_apply_pending_permissions(self):
        base = {"dashboard:view", "simulation:view"}
        pending = {
            "2:dashboard:view": False,
            "2:scenarios:edit": True,
        }
        effective = admin_roles.apply_pending_permissions(base, pending, 2)
        self.assertNotIn("dashboard:view", effective)
        self.assertIn("simulation:view", effective)
        self.assertIn("scenarios:edit", effective)

    def test_compute_role_stats(self):
        all_keys = {"dashboard:view", "simulation:view", "admin-users:view"}
        role_keys = {"dashboard:view"}
        protected = {"admin-users:view"}
        stats = admin_roles.compute_role_stats(all_keys, role_keys, protected)
        self.assertEqual(stats["granted"], 1)
        self.assertEqual(stats["restricted"], 2)
        self.assertEqual(stats["protected_total"], 1)
        self.assertEqual(stats["protected_granted"], 0)


if __name__ == "__main__":
    unittest.main()

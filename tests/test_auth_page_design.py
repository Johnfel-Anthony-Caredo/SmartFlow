import unittest
from pathlib import Path


LOGIN_PATH = Path("pages/login.py")
REGISTER_PATH = Path("pages/register.py")
AUTH_CSS_PATH = Path("assets/auth.css")


class TestAuthPageDesign(unittest.TestCase):
    def test_login_and_register_use_split_auth_shell(self):
        for page_path in (LOGIN_PATH, REGISTER_PATH):
            text = page_path.read_text(encoding="utf-8")
            self.assertIn("auth-shell", text)
            self.assertIn("auth-visual-panel", text)
            self.assertIn("auth-form-panel", text)
            self.assertIn("auth-traffic-scene", text)
            self.assertIn("auth-brand-mark", text)

    def test_auth_hero_nav_includes_dashboard_cta(self):
        login_text = LOGIN_PATH.read_text(encoding="utf-8")
        register_text = REGISTER_PATH.read_text(encoding="utf-8")

        self.assertIn("Open dashboard", login_text)
        self.assertIn("Open dashboard", register_text)
        self.assertIn("auth-back-link", login_text)
        self.assertIn("auth-back-link", register_text)

    def test_login_showcase_copy_matches_screenshot_direction(self):
        login_text = LOGIN_PATH.read_text(encoding="utf-8")

        self.assertIn("Tagum City main intersection", login_text)
        self.assertIn("Coordinate live SUMO traffic with confidence.", login_text)
        self.assertNotIn("Tagum intersection simulation", login_text)
        self.assertNotIn("Live traffic control workspace", login_text)

    def test_existing_callback_ids_are_preserved(self):
        login_text = LOGIN_PATH.read_text(encoding="utf-8")
        register_text = REGISTER_PATH.read_text(encoding="utf-8")

        for expected_id in ("username-input", "password-input", "login-btn", "login-error"):
            self.assertIn(expected_id, login_text)

        for expected_id in (
            "fullname-input",
            "reg-username-input",
            "reg-password-input",
            "reg-confirm-input",
            "email-input",
            "register-btn",
            "register-error",
            "register-success",
        ):
            self.assertIn(expected_id, register_text)

    def test_login_and_register_use_shared_polished_field_system(self):
        for page_path in (LOGIN_PATH, REGISTER_PATH):
            text = page_path.read_text(encoding="utf-8")
            self.assertIn("auth-form-card", text)
            self.assertIn("auth-form-content", text)
            self.assertIn("auth-field", text)
            self.assertIn("auth-field-shell", text)
            self.assertIn("auth-field-hint", text)
            self.assertIn("input-field", text)

    def test_register_form_groups_fields_into_clear_sections(self):
        text = REGISTER_PATH.read_text(encoding="utf-8")
        self.assertIn("auth-form-section", text)
        self.assertIn("Identity", text)
        self.assertIn("Account", text)
        self.assertIn("Security", text)

    def test_auth_css_has_polished_split_layout_and_responsive_fallback(self):
        css = AUTH_CSS_PATH.read_text(encoding="utf-8")
        self.assertIn(".auth-shell", css)
        self.assertIn(".auth-visual-panel", css)
        self.assertIn(".auth-form-panel", css)
        self.assertIn(".auth-traffic-scene", css)
        self.assertIn("@keyframes authSceneDrift", css)
        self.assertIn("@media (max-width: 900px)", css)
        self.assertIn("grid-template-columns", css)
        self.assertIn("width: min(1120px, calc(100vw - 48px))", css)
        self.assertIn("min-height: 100vh", css)
        self.assertIn("border-radius: 30px", css)
        self.assertIn("background-clip: padding-box", css)
        self.assertNotIn("-webkit-box-shadow: 0 0 0 1000px #ffffff inset !important", css)

    def test_auth_showcase_scene_matches_framed_reference(self):
        css = AUTH_CSS_PATH.read_text(encoding="utf-8")

        self.assertIn("min-height: 270px", css)
        self.assertIn("border: 1px solid rgba(255, 255, 255, 0.12)", css)
        self.assertIn("box-shadow: 0 24px 70px rgba(0, 0, 0, 0.32) inset", css)
        self.assertIn("width: 72%", css)
        self.assertIn("height: 76px", css)

    def test_auth_css_controls_custom_field_states(self):
        css = AUTH_CSS_PATH.read_text(encoding="utf-8")
        self.assertIn(".auth-page .auth-field-shell", css)
        self.assertIn(".auth-page .auth-field-shell:focus-within", css)
        self.assertIn(".auth-page .auth-field-shell:hover", css)
        self.assertIn(".auth-page .auth-field-shell.is-error", css)
        self.assertIn(".auth-page .auth-field-shell.is-disabled", css)
        self.assertIn(".auth-page .input-field:-webkit-autofill", css)
        self.assertIn("-webkit-text-fill-color: #102033 !important", css)
        self.assertIn("caret-color: #00b86b !important", css)
        self.assertIn("height: 54px", css)
        self.assertIn("overflow: hidden", css)
        self.assertIn("-webkit-box-shadow: 0 0 0 1000px #eef5ef inset !important", css)
        self.assertNotIn("-webkit-background-clip: text", css)


if __name__ == "__main__":
    unittest.main()

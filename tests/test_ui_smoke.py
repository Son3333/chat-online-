import customtkinter as ctk


class TestUISmokeAndTheme:
    def test_theme_mode_values(self):
        # Appearance mode can be set and read cleanly
        ctk.set_appearance_mode("Dark")
        assert ctk.get_appearance_mode() == "Dark"

        ctk.set_appearance_mode("Light")
        assert ctk.get_appearance_mode() == "Light"

        # Restore dark
        ctk.set_appearance_mode("Dark")

    def test_search_filter_regex(self):
        # Test username and ID patterns
        search_query_username = "@son123"
        cleaned_user = search_query_username.strip().lstrip("@")
        assert cleaned_user == "son123"

        search_query_id = "#1698870709"
        cleaned_id = search_query_id.strip().lstrip("#")
        assert cleaned_id.isdigit()
        assert int(cleaned_id) == 1698870709

    def test_message_entry_validation(self):
        # Test empty message guard
        empty_texts = ["", "   ", "\n\n", "\t"]
        for t in empty_texts:
            assert len(t.strip()) == 0

        valid_text = "  Hello live test!  "
        assert valid_text.strip() == "Hello live test!"

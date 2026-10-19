from iiif_metadata_normalizer.extractor import (
    classify_label, clean_text, normalize_date, normalize_language,
    normalize_place, text_values,
)


def test_text_values_supports_language_maps():
    assert text_values({"en": ["Title"], "fr": ["Titre"]}, "$.label") == [
        {"value": "Title", "language": "en", "json_path": "$.label.en[0]"},
        {"value": "Titre", "language": "fr", "json_path": "$.label.fr[0]"},
    ]


def test_text_values_supports_presentation_2_value_objects():
    assert text_values({"@value": "Livre", "@language": "fr"}, "$.label")[0]["language"] == "fr"


def test_clean_text_removes_html_and_decodes_entities():
    assert clean_text("<p>A&nbsp; B</p>") == "A B"


def test_classify_label_recognizes_project_fields():
    assert classify_label("Date of origin") == "date"
    assert classify_label("Shelfmark") == "identifier"
    assert classify_label("Place of origin") == "place"


def test_normalize_date_handles_full_iso_date():
    value = normalize_date("1450-03-02")
    assert (value["normalized"], value["precision"]) == ("1450-03-02", "day")


def test_normalize_date_handles_noisy_year_range():
    value = normalize_date("1401 – 1500 CE")
    assert (value["start_year"], value["end_year"]) == (1401, 1500)


def test_normalize_date_handles_century():
    value = normalize_date("15th century")
    assert (value["start_year"], value["end_year"], value["precision"]) == (1401, 1500, "century")


def test_normalize_date_preserves_unparsed_value_as_unparsed():
    assert normalize_date("early modern")["normalized"] is None


def test_normalizers_do_not_invent_values():
    assert normalize_place("unknown") is None
    assert normalize_language("Latin") == "la"

"""Descriptive metadata must not become OCR labels merely because it is XML."""
from iiif_metadata_normalizer.reference_text import extract_reference_text_resources


def test_descriptive_xml_is_excluded_but_declared_alto_reference_is_retained():
    metadata = {"@id": "https://example.org/metadata.untl.xml", "format": "text/xml",
                "label": "UNTL Descriptive Metadata"}
    alto = {"@id": "https://example.org/page.alto.xml", "format": "text/xml", "label": "ALTO OCR"}
    document = {"seeAlso": [metadata], "sequences": [{"canvases": [
        {"@id": "https://example.org/canvas/1", "seeAlso": [metadata, alto]}]}]}
    result = extract_reference_text_resources(document, {"manifest_id": "m1"})
    assert len(result) == 1
    assert result[0]["source_url"] == alto["@id"]
    assert result[0]["canvas_id"] == "https://example.org/canvas/1"


def test_inline_page_transcription_remains_an_ocr_reference():
    document = {"items": [{"id": "https://example.org/canvas/1", "type": "Canvas", "annotations": [{"items": [
        {"motivation": "supplementing", "body": {"type": "TextualBody", "value": "Historical page text", "format": "text/plain"}}
    ]}]}]}
    result = extract_reference_text_resources(document, {"manifest_id": "m1"})
    assert len(result) == 1
    assert result[0]["inline_text"] == "Historical page text"


def test_catalogue_html_seealso_is_not_a_transcription_but_full_text_is():
    catalogue = {"id": "https://example.org/catalogue/42", "type": "Text", "format": "text/html",
                 "label": "Object Page in Online Collections Catalog"}
    transcription = {"id": "https://example.org/transcription/42", "type": "Text", "format": "text/html",
                     "label": "Full text transcription"}
    result = extract_reference_text_resources({'seeAlso': [catalogue, transcription]}, {'manifest_id': 'm1'})
    assert len(result) == 1
    assert result[0]['source_url'] == transcription['id']


def test_linked_art_rdf_seealso_is_metadata_even_with_a_textual_mime_prefix():
    resources = [{"id": "https://example.org/id/page/object/12", "type": "Dataset", "format": mime}
                 for mime in ["text/rdf+n3", "text/turtle", "application/rdf+xml"]]
    result = extract_reference_text_resources({'seeAlso': resources}, {'manifest_id': 'm1'})
    assert result == []


def test_generic_dataset_requires_transcription_evidence():
    metadata = {"id": "https://example.org/data/12", "type": "Dataset", "format": "text/plain"}
    text = {"id": "https://example.org/transcription/12", "type": "Dataset", "format": "text/plain",
            "label": "Page transcription"}
    result = extract_reference_text_resources({'seeAlso': [metadata, text]}, {'manifest_id': 'm1'})
    assert len(result) == 1 and result[0]['source_url'] == text['id']


def test_seealso_text_type_alone_does_not_certify_catalogue_ocr():
    resources = [{"id": "https://example.org/data/object/12", "type": "Text"},
                 {"id": "https://example.org/data/object/13", "type": "Text", "format": "application/ld+json"}]
    result = extract_reference_text_resources({'seeAlso': resources}, {'manifest_id': 'm1'})
    assert result == []


def test_explicit_json_transcription_remains_a_reference():
    resource = {"id": "https://example.org/data/page/12", "type": "Text",
                "format": "application/json", "label": "Institution page transcription"}
    result = extract_reference_text_resources({'seeAlso': [resource]}, {'manifest_id': 'm1'})
    assert len(result) == 1 and result[0]['source_url'] == resource['id']

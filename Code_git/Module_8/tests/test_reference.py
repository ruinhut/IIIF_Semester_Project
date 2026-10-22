"""Prevent document titles from masquerading as OCR labels."""

from iiif_image_downloader.reference import _is_text_content_type, _to_plain_text
import pytest


def test_hocr_metadata_only_is_empty():
    payload = b'<html><head><title>book_00001</title><style>body {color:black}</style></head><body><div class="ocr_page"></div><script>test()</script></body></html>'
    assert _to_plain_text(payload, "text/vnd.hocr+html") == ""


def test_hocr_keeps_recognized_words_but_not_filename():
    payload = b'<html><head><title>book_00002</title></head><body><span class="ocrx_word">Actual</span> <span class="ocrx_word">words</span></body></html>'
    assert _to_plain_text(payload, "text/vnd.hocr+html") == "Actual words"


@pytest.mark.parametrize("version", ["v2", "v4"])
def test_alto_reads_page_words_and_entities_without_processing_metadata(version):
    payload = ('<a:alto xmlns:a="http://www.loc.gov/standards/alto/ns-' + version + '#">'
        '<a:Description><a:MeasurementUnit>pixel</a:MeasurementUnit>'
        '<a:processingStepSettings>model=deu_latf filename.tif</a:processingStepSettings></a:Description>'
        '<a:Layout><a:Page><a:TextBlock><a:TextLine>'
        '<a:String CONTENT="AT&amp;T"/><a:String CONTENT="reader&apos;s"/></a:TextLine>'
        '<a:TextLine><a:String CONTENT="Second line"/></a:TextLine>'
        '</a:TextBlock></a:Page></a:Layout></a:alto>').encode()
    assert _to_plain_text(payload, "application/alto+xml") == "AT&T reader's\nSecond line"


def test_metadata_only_alto_is_empty_and_vendor_xml_is_supported():
    payload = b'<alto><Description><sourceImageInformation>book.tif</sourceImageInformation></Description><Layout><Page/></Layout></alto>'
    assert _to_plain_text(payload, "application/alto+xml") == ""
    assert _is_text_content_type("application/alto+xml")

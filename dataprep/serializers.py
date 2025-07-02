from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.transforms.serializer.html import HTMLDocSerializer
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from docling_core.transforms.chunker.hierarchical_chunker import TripletTableSerializer

INPUT_DOC = Path("sample-data/ub-pldi25.pdf")

start_html_cue = "1 Introduction"
stop_html_cue = "2 Undefined Behavior"

start_md_cue = "2 Undefined Behavior"
stop_md_cue = "2.1 Disabling Exploitation of Undefined Behavior"

def html_serializer():
    converter = DocumentConverter()
    doc = converter.convert(source=INPUT_DOC).document

    serializer = HTMLDocSerializer(doc=doc)
    ser_result = serializer.serialize()
    ser_text = ser_result.text

    print(ser_text[ser_text.find(start_html_cue) : ser_text.find(stop_html_cue)])

def markdown_serializer():
    converter = DocumentConverter()
    doc = converter.convert(source=INPUT_DOC).document

    serializer = MarkdownDocSerializer(doc=doc)
    ser_result = serializer.serialize()
    ser_text = ser_result.text

    print(ser_text[ser_text.find(start_md_cue) : ser_text.find(stop_md_cue)])

def markdown_serializer_custom():
    converter = DocumentConverter()
    doc = converter.convert(source=INPUT_DOC).document

    serializer = MarkdownDocSerializer(
        doc=doc,
        table_serializer=TripletTableSerializer(),
    )

    ser_result = serializer.serialize()
    ser_text = ser_result.text

    print(ser_text[ser_text.find(start_md_cue) : ser_text.find(stop_md_cue)])


if __name__ == "__main__":
    html_serializer()
    #markdown_serializer()
    #markdown_serializer_custom()


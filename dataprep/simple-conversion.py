from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"  # document URL

converter = DocumentConverter()
doc = converter.convert(source).document

print(doc.export_to_markdown())

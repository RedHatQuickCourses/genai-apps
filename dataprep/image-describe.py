from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import smolvlm_picture_description
from docling_core.types.doc.document import PictureDescriptionData

INPUT_DOC = "sample-data/docling-paper.pdf"
OUTFILE = "/tmp/image-describe.html"

def main():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_picture_description = True
    pipeline_options.picture_description_options = (
        smolvlm_picture_description
    )
    pipeline_options.picture_description_options.prompt = (
        "Describe the image in three sentences. Be consise and accurate."
    )
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )

    doc = converter.convert(INPUT_DOC).document

    html_buffer = []
    # display the first 5 pictures and their captions and annotations:
    for pic in doc.pictures[:5]:
        html_item = (
            f"<h3>Picture <code>{pic.self_ref}</code></h3>"
            f'<img src="{pic.image.uri!s}" /><br />'
            f"<h4>Caption</h4>{pic.caption_text(doc=doc)}<br />"
        )
        for annotation in pic.annotations:
            if not isinstance(annotation, PictureDescriptionData):
                continue
            html_item += (
                f"<h4>Annotations ({annotation.provenance})</h4>{annotation.text}<br />\n"
            )
        html_buffer.append(html_item)

    try:
        with open(OUTFILE, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html>\n")  # Add a basic HTML doctype
            f.write("<html>\n<head>\n<title>Picture Descriptions</title>\n</head>\n<body>\n")
            for item in html_buffer:
                f.write(item)
            f.write("</body>\n</html>")
        print(f"Content successfully written to {OUTFILE}")
    except IOError as e:
        print(f"Error writing to file {OUTFILE}: {e}")

if __name__ == "__main__":
    main()
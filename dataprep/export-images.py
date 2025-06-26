from pathlib import Path

# Docling imports
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import PictureItem

INPUT_FILE = "sample-data/penrose.pdf"
OUTPUT_DIR = "/tmp/export-images/"

input_file = Path(INPUT_FILE)
output_path = Path(OUTPUT_DIR)
    
output_path.mkdir(parents=True, exist_ok=True)

def main():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    conv_res = doc_converter.convert(input_file)
    out_file_name = conv_res.input.file.stem

    for page_no, page in conv_res.document.pages.items():
        page_no = page.page_no
        page_image_filename = output_path / f"{out_file_name}-page-{page_no}.png"

        with page_image_filename.open("wb") as fp:
            page.image.pil_image.save(fp, format="PNG")
    
    picture_counter = 0
    for element, _level in conv_res.document.iterate_items():
        if isinstance(element, PictureItem):
            picture_counter += 1
            element_image_filename = (
                output_path / f"{out_file_name}-picture-{picture_counter}.png"
            )
            with element_image_filename.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")

if __name__ == "__main__":
    main()
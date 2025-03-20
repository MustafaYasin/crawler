from docling.document_converter import DocumentConverter
from utils.sitemap import get_sitemap_urls

converter = DocumentConverter()

sitemap_urls = get_sitemap_urls("https://ds4sd.github.io/docling/")
conv_results_iter = converter.convert_all(sitemap_urls)

docs = []
for result in conv_results_iter:
    if result.document:
        document = result.document
        docs.append(document)
from docling.document_converter import DocumentConverter

source = "/Users/mustafayasin/Desktop/2411.14974v2.pdf"
converter = DocumentConverter()
print("I was here")
result = converter.convert(source)

# Save to a file instead of printing to terminal
output_path = "/Users/mustafayasin/Desktop/converted_document.md"
with open(output_path, "w", encoding="utf-8") as file:
    file.write(result.document.export_to_markdown())

print(f"Markdown saved to {output_path}")
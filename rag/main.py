from docling.document_converter import DocumentConverter
from utils.sitemap import get_sitemap_urls
import os
import time
import xml.etree.ElementTree as ET
import requests
from urllib.parse import urlparse, parse_qs

def extract_urls_from_sitemap(sitemap_url, timeout=60):
    """Extract all content URLs from a sitemap file"""
    try:
        print(f"Fetching content URLs from: {sitemap_url}")
        response = requests.get(sitemap_url, timeout=timeout)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        # Handle namespace if present
        namespaces = (
            {"ns": root.tag.split("}")[0].strip("{")} if "}" in root.tag else ""
        )

        # Extract URLs
        if namespaces:
            urls = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
        else:
            urls = [elem.text for elem in root.findall(".//loc")]

        return urls
    except Exception as e:
        print(f"Error extracting URLs from {sitemap_url}: {e}")
        return []

# Create output directory
output_dir = "converted_pages"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Get sitemap index URLs
base_url = "https://www.euwid-recycling.de/"
sitemap_index_urls = get_sitemap_urls(base_url, timeout=60)
print(f"Found {len(sitemap_index_urls)} sitemap entries")

# Extract all content URLs from each sitemap
all_content_urls = []
for sitemap_url in sitemap_index_urls:
    # Check if this looks like a sitemap URL rather than a content URL
    parsed_url = urlparse(sitemap_url)
    query_params = parse_qs(parsed_url.query)

    if 'sitemap' in query_params:
        # This is likely a sitemap file, extract content URLs from it
        content_urls = extract_urls_from_sitemap(sitemap_url)
        print(f"Found {len(content_urls)} content URLs in {sitemap_url}")
        all_content_urls.extend(content_urls)
        time.sleep(1)  # Be nice to the server
    else:
        # This might be a direct content URL
        all_content_urls.append(sitemap_url)

# Remove duplicates while preserving order
unique_content_urls = []
for url in all_content_urls:
    if url not in unique_content_urls:
        unique_content_urls.append(url)

print(f"Total unique content URLs found: {len(unique_content_urls)}")

# Now process each content URL
converter = DocumentConverter()
successful_conversions = 0

for i, url in enumerate(unique_content_urls):
    try:
        print(f"Converting {i+1}/{len(unique_content_urls)}: {url}")

        # Convert the page
        result = converter.convert(url)

        if result and hasattr(result, 'document') and result.document:
            # Create a filename based on the URL
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            if not path:
                path = "index"
            filename = path.replace('/', '_')
            if parsed.query:
                # Add a short hash of the query string to differentiate pages
                query_hash = str(hash(parsed.query))[-6:]
                filename += f"_{query_hash}"
            if not filename.endswith(".md"):
                filename += ".md"

            output_path = os.path.join(output_dir, filename)

            # Save the markdown to a file
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(result.document.export_to_markdown())

            print(f"Saved to {output_path}")
            successful_conversions += 1
        else:
            print(f"No document content for {url}")

        # Add a delay to be nice to the server
        time.sleep(2)

    except Exception as e:
        print(f"Error processing {url}: {e}")

print(f"Crawling complete. Successfully converted {successful_conversions} out of {len(unique_content_urls)} URLs.")
import xml.etree.ElementTree as ET
from typing import List
from urllib.parse import urljoin
import time

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def get_sitemap_urls(base_url: str, sitemap_filename: str = "sitemap.xml", timeout: int = 30, max_retries: int = 3) -> List[str]:
    """
    Get all URLs from a sitemap.

    Args:
        base_url: The base URL of the website
        sitemap_filename: The filename of the sitemap
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries for failed requests

    Returns:
        List of URLs found in the sitemap
    """
    try:
        sitemap_url = urljoin(base_url, sitemap_filename)
        print(f"Trying to fetch sitemap from: {sitemap_url}")

        # Set up session with retry logic
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=1  # 1, 2, 4 seconds between retries
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Try to fetch the sitemap
        print(f"Attempting to fetch sitemap with {timeout}s timeout...")
        response = session.get(sitemap_url, timeout=timeout)

        # If sitemap not found, try common variations
        if response.status_code == 404:
            alternates = ["sitemap_index.xml", "sitemap-index.xml", "sitemapindex.xml"]
            for alt in alternates:
                alt_url = urljoin(base_url, alt)
                print(f"Sitemap not found, trying alternative: {alt_url}")
                response = session.get(alt_url, timeout=timeout)
                if response.status_code == 200:
                    break

        # If still not found, return just the base URL
        if response.status_code == 404:
            print("No sitemap found. Using base URL only.")
            return [base_url.rstrip("/")]

        response.raise_for_status()

        # Parse the XML
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

        # If no URLs found, try common alternative formats
        if not urls and root.tag.endswith('sitemapindex'):
            print("Found sitemap index, fetching individual sitemaps...")
            sitemap_urls = []
            if namespaces:
                sitemap_urls = [elem.text for elem in root.findall(".//ns:sitemap/ns:loc", namespaces)]
            else:
                sitemap_urls = [elem.text for elem in root.findall(".//sitemap/loc")]

            # Fetch each individual sitemap
            all_urls = []
            for sitemap in sitemap_urls:
                print(f"Fetching sitemap: {sitemap}")
                try:
                    sub_response = session.get(sitemap, timeout=timeout)
                    sub_response.raise_for_status()
                    sub_root = ET.fromstring(sub_response.content)

                    # Handle namespace in the sub-sitemap
                    sub_namespaces = (
                        {"ns": sub_root.tag.split("}")[0].strip("{")} if "}" in sub_root.tag else ""
                    )

                    if sub_namespaces:
                        sub_urls = [elem.text for elem in sub_root.findall(".//ns:loc", sub_namespaces)]
                    else:
                        sub_urls = [elem.text for elem in sub_root.findall(".//loc")]

                    all_urls.extend(sub_urls)
                    # Add a small delay between requests
                    time.sleep(1)
                except Exception as e:
                    print(f"Error fetching sub-sitemap {sitemap}: {e}")

            if all_urls:
                return all_urls

        # If we still have no URLs, return just the base URL
        if not urls:
            print("No URLs found in sitemap. Using base URL only.")
            return [base_url.rstrip("/")]

        return urls

    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch sitemap: {str(e)}")
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse sitemap XML: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error processing sitemap: {str(e)}")


if __name__ == "__main__":
    # Test the function
    urls = get_sitemap_urls("https://www.euwid-recycling.de/", timeout=60)
    print(f"Found {len(urls)} URLs")
    for i, url in enumerate(urls[:5]):  # Print first 5 URLs
        print(f"{i+1}: {url}")
    if len(urls) > 5:
        print(f"... and {len(urls) - 5} more URLs")
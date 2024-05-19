"""
Web Crawler

This module provides a web crawler that crawls a specified domain and saves the crawled URLs to a file in the specified format (JSON, CSV, or TXT).

Usage:
    python crawler.py <domain> [--format <output_format>] [--output-dir <output_dir>] [--user-agent <user_agent>] [--delay <delay>]

Options:
    -format: Output file format (json, csv, txt) (default: txt)
    --output-dir: Output directory to store the output file (default: output)
    --user-agent: User agent string (default: None)
    --delay: Delay between requests in seconds (default: 0)
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Set
import typer
import json
import csv
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from pathlib import Path

app = typer.Typer()

"""
    Fetch the HTML content of the given URL.

    Args:
        url (str): The URL to fetch.
        client (httpx.AsyncClient): The HTTP client to use for making requests.
        user_agent (str, optional): The User-Agent header to send with the request. Defaults to None.
        delay (float, optional): The delay in seconds before making the request. Defaults to 0.

    Returns:
        str: The HTML content of the URL.
"""

async def fetch_html(url: str, client: httpx.AsyncClient, user_agent: str = None, delay: float = 0) -> str:
    try:
        await asyncio.sleep(delay)
        headers = {"User-Agent": user_agent} if user_agent else None
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            print(f"Access denied for URL: {url}. The website does not allow crawlers.")
        else:
            print(f"HTTP error occurred for URL: {url}. Status code: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"An error occurred while requesting URL: {url}. Error: {str(e)}")
    return ""

"""
    Parse the HTML content and extract the links.

    Args:
        html (str): The HTML content to parse.
        base_url (str): The base URL to resolve relative links.

    Returns:
        Set[str]: A set of extracted links.
"""

async def parse_links(html: str, base_url: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.startswith("http"):
            links.add(href)
        elif href:
            links.add(f"{base_url}{href}")
    return links

"""
    Check if the given URL is allowed to be crawled according to the robots.txt file.

    Args:
        url (str): The URL to check.
        robots_txt_url (str): The URL of the robots.txt file.
        client (httpx.AsyncClient): The HTTP client to use for making requests.

    Returns:
        bool: True if the URL is allowed to be crawled, False otherwise.
    """

async def is_crawlable(url: str, robots_txt_url: str, client: httpx.AsyncClient) -> bool:
    try:
        robots_txt = await client.get(robots_txt_url)
        if robots_txt.status_code == 200:
            rp = RobotFileParser()
            rp.parse(robots_txt.text.splitlines())
            return rp.can_fetch("*", url)
    except httpx.RequestError:
        pass
    return True

"""
    Perform the web crawling process.

    Args:
        base_url (str): The base URL to start crawling from.
        max_depth (int): The maximum depth to crawl.
        output_dir (str): The output directory to store the output file.
        output_format (str): The format of the output file (json, csv, txt).
        user_agent (str, optional): The User-Agent header to send with the requests. Defaults to None.
        delay (float, optional): The delay in seconds between requests. Defaults to 0.
    """


async def crawl(base_url: str, max_depth: int, output_file: str,format: str, output_dir: str, user_agent: str = None, delay: float = 0):

    visited_urls = set()
    queue = asyncio.Queue()
    await queue.put((base_url, 0))

    # Create the output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient() as client:
        while not queue.empty():
            url, depth = await queue.get()
            if url in visited_urls or depth >= max_depth:
                continue
            visited_urls.add(url)
            print(f"Crawling: {url}")

            # Check if the URL is allowed to be crawled
            parsed_url = urlparse(url)
            robots_txt_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            if not await is_crawlable(url, robots_txt_url, client):
                print(f"Skipping URL: {url}. Not allowed by robots.txt.")
                continue

            html = await fetch_html(url, client, user_agent, delay)
            if html:
                links = await parse_links(html, base_url)
                for link in links:
                    await queue.put((link, depth + 1))

            # Write the crawled URL to the output file based on the specified format
            output_file_path = output_path / output_file
            if format == "json":
                with open(output_file_path, "a") as file:
                    json.dump({"url": url}, file)
                    file.write("\n")
            elif format == "csv":
                with open(output_file_path, "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([url])
            else:  # Default to TXT format
                with open(output_file_path, "a") as file:
                    file.write(url + "\n")


"""
Start the web crawling process.

    Args:
        domain (str): The domain name to crawl.
        output_file (str, optional): The output file to store the crawled URLs. Defaults to "crawled_urls.txt".
        output_format (str, optional): The format of the output file (json, csv, txt). Defaults to "txt".
        output_dir (str, optional): The output directory to store the output file. Defaults to "output".
        user_agent (str, optional): The User-Agent header to send with the requests. Defaults to None.
        delay (float, optional): The delay in seconds between requests. Defaults to 0.
 """

@app.command()
def start_crawl(
    domain: str = typer.Argument(..., help="Domain name to crawl"),
    user_agent: str = typer.Option(None, help="User agent string"),
    format: str = typer.Option("txt", help="Output file format (json, csv, txt)"),
    output_dir= typer.Option("output",help = "Output directory , where to save the file"),
    max_depth: int = typer.Option(2, help="Max depth for crawling"),
    delay: float = typer.Option(0, help="Delay between requests (in seconds)")
):
    if (domain.startswith("https://")):
            base_url = domain
            output_file_name = domain.split("/")
            asyncio.run(crawl(base_url, max_depth=max_depth, user_agent=user_agent, delay=delay, output_file= output_file_name[2] + "." + format, output_dir=output_dir, format=format))
    else:
        base_url = f"https://{domain}"
        output_file_name = domain.split("/")
        asyncio.run(crawl(base_url, max_depth=max_depth, user_agent=user_agent, delay=delay, output_file= output_file_name[0] + "." + format, output_dir=output_dir, format=format))
    print(f"Crawling completed")

if __name__ == "__main__":
    app()



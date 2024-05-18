import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Set
import typer
import json
import csv
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

app = typer.Typer()

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


async def crawl(base_url: str, max_depth: int, output_file: str, format: str, user_agent: str = None, delay: float = 0):
    visited_urls = set()
    queue = asyncio.Queue()
    await queue.put((base_url, 0))

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
            if format == "json":
                with open(output_file, "a") as file:
                    json.dump({"url": url}, file)
                    file.write("\n")
            elif format == "csv":
                with open(output_file, "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([url])
            else:  # Default to TXT format
                with open(output_file, "a") as file:
                    file.write(url + "\n")


@app.command()
def start_crawl(
    domain: str = typer.Argument(..., help="Domain name to crawl"),
    user_agent: str = typer.Option(None, help="User agent string"),
    format: str = typer.Option("txt", help="Output file format (json, csv, txt)"),
    max_depth: int = typer.Option(10, help="Max depth for crawling"),
    delay: float = typer.Option(0, help="Delay between requests (in seconds)")
):
    if (domain.startswith("https://")):
            base_url = domain
            output_file_name = domain.split("/")
            asyncio.run(crawl(base_url, max_depth=max_depth, user_agent=user_agent, delay=delay, output_file=output_file_name[2], format=format))
    else:
        base_url = f"https://{domain}"
        output_file_name = domain.split("/")
        asyncio.run(crawl(base_url, max_depth=max_depth, user_agent=user_agent, delay=delay, output_file=output_file_name[0], format=format))
    print(f"Crawling completed")

if __name__ == "__main__":
    app()

# Web Crawler

This is a Python-based web crawler that allows you to crawl a specified domain and save the crawled URLs to a file in various formats (JSON, CSV, or TXT).

## Features

- Crawls a specified domain and extracts URLs
-  different output file formats (JSON, CSV, TXT)
- Configurable output directory
- Customizable User-Agent header
- Adjustable delay between requests
- Quiet mode to suppress printing of parsed URLs
- Follows robots.txt rules to determine if a URL is allowed to be crawled
- Logs errors and status messages

## Prerequisites

- Python 3.7 or higher
- Required Python packages listed in requirements.txt

## Installation

- Clone the repository or download the source code:
  
```bash
git clone https://github.com/iridhicode/web-crawler.git
```

- Navigate to the project directory:
  
```bash
cd web-crawler
```

- Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

To run the web crawler, use the following command:

```bash
python crawler.py <domain> [--format <output_format>] [--output-dir <output_dir>] [--user-agent <user_agent>] [--delay <delay>] [--quiet <quiet>]
```

### Arguments:

<domain>:The domain name to crawl (required).

### Options:

--format <output_format>: Output file format. Supported values: json, csv, txt (default: txt).
--output-dir <output_dir>: Output directory to store the output file (default: output).
--user-agent <user_agent>: User-Agent header to send with the requests (default: None).
--delay <delay>: Delay between requests in seconds (default: 0).
--quiet <quiet>: Enable quiet mode to suppress printing of parsed URLs (default: False).

### Example usage:

```bash
python main.py example.com --format json --output-dir /path/to/output --user-agent "MyCustomCrawler" --delay 1 --quiet True
```

### Output

The crawled URLs will be saved to a file in the specified output directory. The output file name will include the domain name and a timestamp in the format YYYYMMDD_HHMMSS.

Example output file names:

- JSON: example.com_20230520_123456.json
- CSV: example.com_20230520_123456.csv
- TXT: example.com_20230520_123456.txt

### Logging
The web crawler logs errors and status messages using the Python logging module. The log level is set to DEBUG by default, which can be adjusted in the code if needed.


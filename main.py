# main.py
import sys
import asyncio
from crawl import crawl_site_async
from csv_report import write_csv_report


async def main():
    args = sys.argv

    if len(args) != 4:
        print("usage: uv run main.py URL max_concurrency max_pages")
        sys.exit(1)

    base_url = args[1]

    try:
        max_concurrency = int(args[2])
        max_pages = int(args[3])
    except ValueError:
        print("max_concurrency and max_pages must be integers")
        sys.exit(1)

    print(f"Starting async crawl of: {base_url}")
    print(f"Max concurrency: {max_concurrency}, Max pages: {max_pages}")

    page_data = await crawl_site_async(
        base_url,
        max_concurrency=max_concurrency,
        max_pages=max_pages,
    )
    write_csv_report(page_data)
    sys.exit(0)


    # for page in page_data.values():
    #     if not page:
    #         continue
    #     print(f"Found {len(page['outgoing_links'])} outgoing links on {page['url']}")


if __name__ == "__main__":
    asyncio.run(main())

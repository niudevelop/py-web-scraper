# crawl.py
from urllib.parse import urlparse, urljoin
import asyncio
from bs4 import BeautifulSoup
import aiohttp


def normalize_url(url: str) -> str:
    parsed_url = urlparse(url)
    full_path = f"{parsed_url.netloc}{parsed_url.path}".rstrip("/")
    return full_path.lower()


def get_h1_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h1_tag = soup.find("h1")
    return h1_tag.get_text(strip=True) if h1_tag else ""


def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    main_section = soup.find("main")
    if main_section:
        first_p = main_section.find("p")
    else:
        first_p = soup.find("p")

    return first_p.get_text(strip=True) if first_p else ""


def get_urls_from_html(html: str, base_url: str) -> list[str]:
    urls: list[str] = []
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a")

    for anchor in anchors:
        href = anchor.get("href")
        if not href:
            continue
        try:
            absolute_url = urljoin(base_url, href)
            urls.append(absolute_url)
        except Exception as e:
            print(f"{str(e)}: {href}")

    return urls


def get_images_from_html(html: str, base_url: str) -> list[str]:
    image_urls: list[str] = []
    soup = BeautifulSoup(html, "html.parser")
    images = soup.find_all("img")

    for img in images:
        src = img.get("src")
        if not src:
            continue
        try:
            absolute_url = urljoin(base_url, src)
            image_urls.append(absolute_url)
        except Exception as e:
            print(f"{str(e)}: {src}")

    return image_urls


def extract_page_data(html: str, page_url: str) -> dict:
    return {
        "url": page_url,
        "h1": get_h1_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }


class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrency: int = 3, max_pages: int = 100):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc

        # Page store: key = normalized_url, value = page_info dict (or None while reserved)
        self.page_data: dict[str, dict | None] = {}

        self.lock = asyncio.Lock()

        self.max_concurrency = max(1, int(max_concurrency))
        self.semaphore = asyncio.Semaphore(self.max_concurrency)

        self.max_pages = max(1, int(max_pages))
        self.should_stop = False
        self.all_tasks: set[asyncio.Task] = set()

        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _track_task(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro)
        async with self.lock:
            self.all_tasks.add(task)
        return task

    async def _run_and_untrack(self, url: str):
        task = asyncio.current_task()
        try:
            await self.crawl_page(url)
        finally:
            async with self.lock:
                if task is not None:
                    self.all_tasks.discard(task)

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            if self.should_stop:
                return False

            if normalized_url in self.page_data:
                return False

            if len(self.page_data) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")

                current = asyncio.current_task()
                for t in list(self.all_tasks):
                    if t is not None and t is not current and not t.done():
                        t.cancel()
                return False

            # Reserve the slot immediately (prevents duplicates + enforces max_pages under concurrency)
            self.page_data[normalized_url] = None
            return True

    async def get_html(self, url: str) -> str | None:
        if not self.session:
            return None

        try:
            async with self.session.get(
                url, headers={"User-Agent": "BootCrawler/1.0"}
            ) as response:
                if response.status > 399:
                    print(f"Error: HTTP {response.status} for {url}")
                    return None

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    print(f"Error: Non-HTML content {content_type} for {url}")
                    return None

                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    async def crawl_page(self, current_url: str):
        if self.should_stop:
            return

        current_url_obj = urlparse(current_url)
        if current_url_obj.netloc != self.base_domain:
            return

        normalized_url = normalize_url(current_url)
        is_new = await self.add_page_visit(normalized_url)
        if not is_new:
            return

        # PRINT EARLY: guarantees one line per reserved page even if cancelled later
        print(f"Crawling {current_url}")

        try:
            async with self.semaphore:
                if self.should_stop:
                    return

                html = await self.get_html(current_url)
                if html is None:
                    return

                page_info = extract_page_data(html, current_url)
                async with self.lock:
                    self.page_data[normalized_url] = page_info

                next_urls = get_urls_from_html(html, self.base_url)

            tasks: list[asyncio.Task] = []
            for next_url in next_urls:
                if self.should_stop:
                    break
                tasks.append(await self._track_task(self._run_and_untrack(next_url)))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        finally:
            # KEEP THE RESERVED ENTRY: replace None with a placeholder instead of deleting it
            async with self.lock:
                if (
                    normalized_url in self.page_data
                    and self.page_data[normalized_url] is None
                ):
                    self.page_data[normalized_url] = {
                        "url": current_url,
                        "h1": "",
                        "first_paragraph": "",
                        "outgoing_links": [],
                        "image_urls": [],
                    }

    async def crawl(self) -> dict[str, dict | None]:
        root_task = await self._track_task(self._run_and_untrack(self.base_url))
        await asyncio.gather(root_task, return_exceptions=True)
        return self.page_data


async def crawl_site_async(
    base_url: str, max_concurrency: int = 3, max_pages: int = 100
):
    async with AsyncCrawler(
        base_url, max_concurrency=max_concurrency, max_pages=max_pages
    ) as crawler:
        return await crawler.crawl()

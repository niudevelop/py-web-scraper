import unittest
from crawl import (
    extract_page_data,
    normalize_url,
    get_h1_from_html,
    get_first_paragraph_from_html,
    get_urls_from_html,
    get_images_from_html,
)


class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = "https://blog.boot.dev/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_get_h1_from_html_basic(self):
        input_body = "<html><body><h1>Test Title</h1></body></html>"
        actual = get_h1_from_html(input_body)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_h1_from_html_basic(self):
        input_body = "<html><body><h1>Test Title</h1></body></html>"
        actual = get_h1_from_html(input_body)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_h1_from_html_first_h1_when_multiple(self):
        input_body = "<html><body><h1>First</h1><h1>Second</h1></body></html>"
        actual = get_h1_from_html(input_body)
        expected = "First"
        self.assertEqual(actual, expected)

    def test_get_h1_from_html_none_when_missing(self):
        input_body = "<html><body><p>No title here</p></body></html>"
        actual = get_h1_from_html(input_body)
        self.assertEqual(actual, "")

    # --- get_first_paragraph_from_html tests (>= 3) ---

    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_falls_back_to_body(self):
        input_body = (
            "<html><body><p>First body paragraph.</p><p>Second.</p></body></html>"
        )
        actual = get_first_paragraph_from_html(input_body)
        expected = "First body paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_none_when_missing(self):
        input_body = "<html><body><main><div>No paragraphs</div></main></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        self.assertEqual(actual, "")

    def test_get_urls_from_html_absolute(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body><a href="https://blog.boot.dev"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://blog.boot.dev"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_relative(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://blog.boot.dev/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute(self):
        input_url = "https://blog.boot.dev"
        input_body = (
            '<html><body><a href="https://blog.boot.dev">Boot</a></body></html>'
        )
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://blog.boot.dev"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_relative(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body><a href="/posts/1">Post</a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://blog.boot.dev/posts/1"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_multiple_links(self):
        input_url = "https://example.com"
        input_body = """
            <html><body>
                <a href="/a">A</a>
                <a href="https://other.com/b">B</a>
            </body></html>
        """
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://example.com/a", "https://other.com/b"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_absolute(self):
        input_url = "https://example.com"
        input_body = '<html><body><img src="https://example.com/img.png"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://example.com/img.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_relative(self):
        input_url = "https://example.com"
        input_body = '<html><body><img src="/images/logo.png"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://example.com/images/logo.png"]
        self.assertEqual(actual, expected)
    def test_get_images_from_html_ignores_missing_src(self):
        input_url = "https://example.com"
        input_body = "<html><body><img alt='no src'></body></html>"
        actual = get_images_from_html(input_body, input_url)
        expected = []
        self.assertEqual(actual, expected)


    def test_get_images_from_html_mixed_valid_and_invalid(self):
        input_url = "https://example.com"
        input_body = """
            <html><body>
                <img src="/valid.png">
                <img>
                <img src="">
            </body></html>
        """
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://example.com/valid.png"]
        self.assertEqual(actual, expected)


    def test_get_images_from_html_no_images(self):
        input_url = "https://example.com"
        input_body = "<html><body><p>No images here</p></body></html>"
        actual = get_images_from_html(input_body, input_url)
        expected = []
        self.assertEqual(actual, expected)


    def test_get_images_from_html_multiple_images(self):
        input_url = "https://example.com"
        input_body = """
            <html><body>
                <img src="/a.png">
                <img src="https://cdn.example.com/b.jpg">
            </body></html>
        """
        actual = get_images_from_html(input_body, input_url)
        expected = [
            "https://example.com/a.png",
            "https://cdn.example.com/b.jpg",
        ]
        self.assertEqual(actual, expected)

    def test_extract_page_data_basic(self):
        input_url = "https://blog.boot.dev"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://blog.boot.dev",
            "h1": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://blog.boot.dev/link1"],
            "image_urls": ["https://blog.boot.dev/image1.jpg"],
        }
        self.assertEqual(actual, expected)
    def test_extract_page_data_basic(self):
        input_url = "https://blog.boot.dev"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": input_url,
            "h1": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://blog.boot.dev/link1"],
            "image_urls": ["https://blog.boot.dev/image1.jpg"],
        }
        self.assertEqual(actual, expected)


    def test_extract_page_data_missing_h1(self):
        input_url = "https://example.com"
        input_body = "<html><body><p>Paragraph.</p></body></html>"
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(actual["h1"], "")


    def test_extract_page_data_missing_paragraph(self):
        input_url = "https://example.com"
        input_body = "<html><body><h1>Title</h1></body></html>"
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(actual["first_paragraph"], "")


    def test_extract_page_data_main_paragraph_priority(self):
        input_url = "https://example.com"
        input_body = """<html><body>
            <p>Outside.</p>
            <main><p>Main paragraph.</p></main>
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(actual["first_paragraph"], "Main paragraph.")


    def test_extract_page_data_multiple_links(self):
        input_url = "https://example.com"
        input_body = """<html><body>
            <a href="/a">A</a>
            <a href="/b">B</a>
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(
            actual["outgoing_links"],
            ["https://example.com/a", "https://example.com/b"],
        )


    def test_extract_page_data_empty_html(self):
        input_url = "https://example.com"
        input_body = "<html><body></body></html>"
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(actual["h1"], "")
        self.assertEqual(actual["first_paragraph"], "")
        self.assertEqual(actual["outgoing_links"], [])
        self.assertEqual(actual["image_urls"], [])



if __name__ == "__main__":
    unittest.main()

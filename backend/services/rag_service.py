import io
import re
import urllib.parse

import httpx
import pypdf
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi


class RagService:
    @staticmethod
    def clean_text(text: str) -> str:
        """Removes excessive whitespace and formats text cleanly."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def scrape_web_url(cls, url: str) -> dict[str, str]:
        """Scrapes text contents from a given URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10.0)
            response.raise_for_status()
        except Exception as e:
            raise ValueError(f"Failed to fetch URL: {str(e)}")

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get title
        title = soup.title.string if soup.title else ""
        if not title:
            title = url.split("//")[-1].split("/")[0]  # fallback to domain

        title = cls.clean_text(title)

        # Get text content
        raw_text = soup.get_text(separator=" ")
        content = cls.clean_text(raw_text)

        if len(content) < 50:
            raise ValueError("Scraped page content is too short or page failed to load.")

        return {"title": title, "content": content, "url_path": url}

    @staticmethod
    def extract_youtube_video_id(url: str) -> str:
        """Parses video ID from standard, shortened, and shorts YouTube links."""
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.hostname in ("youtu.be", "www.youtu.be"):
            return parsed_url.path.strip("/")

        if parsed_url.hostname in ("youtube.com", "www.youtube.com"):
            if parsed_url.path == "/watch":
                query = urllib.parse.parse_qs(parsed_url.query)
                if "v" in query:
                    return query["v"][0]
            if parsed_url.path.startswith("/shorts/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]

        raise ValueError("Invalid YouTube URL. Could not find Video ID.")

    @classmethod
    def get_youtube_transcript(cls, url: str) -> dict[str, str]:
        """Retrieves transcript subtitle data from YouTube URL."""
        video_id = cls.extract_youtube_video_id(url)

        # 1. Fetch metadata first to get video title if possible
        title = f"YouTube Video ({video_id})"
        try:
            # We hit oembed api to get clean title details
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = httpx.get(oembed_url, timeout=5.0)
            if response.status_code == 200:
                title = response.json().get("title", title)
        except Exception:
            pass  # fallback to video_id title

        # 2. Extract transcript subtitles
        try:
            transcript_list = YouTubeTranscriptApi().fetch(video_id)
            full_text = " ".join([entry.text for entry in transcript_list])
            content = cls.clean_text(full_text)
        except Exception as e:
            # Fallback warning if captions are disabled
            raise ValueError(
                f"Could not retrieve transcripts for video: {str(e)}. "
                "Ensure that standard subtitles are enabled/public for this video."
            )

        return {"title": title, "content": content, "url_path": url}

    @classmethod
    def parse_pdf(cls, file_bytes: bytes, filename: str) -> dict[str, str]:
        """Parses text from raw PDF bytes."""
        pdf_file = io.BytesIO(file_bytes)
        try:
            reader = pypdf.PdfReader(pdf_file)
            extracted_text = []

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_text.append(text)

            content = " ".join(extracted_text)
            content = cls.clean_text(content)

            if not content:
                raise ValueError("PDF file appears to be empty or contains scanned images only (no selectable text).")

            title = filename.rsplit(".", 1)[0]
            return {"title": title, "content": content, "url_path": filename}
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document: {str(e)}")

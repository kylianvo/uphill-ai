import logging
import os

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from markitdown import MarkItDown
from qdrant_client import QdrantClient

from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Map local files to their original URLs
FILES_TO_INDEX = {
    "/Users/vietvo/Downloads/Book Club_ Training For The Uphill Athlete - Evoke Endurance.html": "https://evokeendurance.com/resources/book-club-training-for-the-uphill-athlete/",
    "/Users/vietvo/Downloads/PROS AND CONS OF RPE AND HEART RATE IN TRAINING.html": "https://evokeendurance.com/resources/pros-and-cons-of-using-rpe-and-heart-rate-in-training/",
    "/Users/vietvo/Downloads/Why Even Ultra Runners Need Speed Work - Evoke Endurance.html": "https://evokeendurance.com/resources/why-even-ultra-runners-need-speed-work/",
    "/Users/vietvo/Downloads/Treadmill Season - Evoke Endurance.html": "https://evokeendurance.com/resources/treadmill-season/",
    "/Users/vietvo/Downloads/Muscular Endurance_ All You Need to Know - Evoke Endurance.html": "https://evokeendurance.com/resources/muscular-endurance-all-you-need-to-know/",
    "/Users/vietvo/Downloads/How Training Works - Evoke Endurance.html": "https://evokeendurance.com/resources/how-training-works/",
    "/Users/vietvo/Downloads/Setting Your Heart Rate Zones - Evoke Endurance.html": "https://evokeendurance.com/resources/setting-your-hear-rate-zones/",
}

COLLECTION_NAME = "uphill_athlete_materials"
EMBEDDING_MODEL = "models/gemini-embedding-2"
EMBEDDING_DIMENSIONS = 3072


def main():
    if not settings.GEMINI_API_KEY and not settings.GEMINI_API_KEYS:
        logger.error("GEMINI_API_KEY is missing. Please set it in .env")
        return

    # Use the first key for embedding initialization
    api_key = settings.get_next_gemini_key()

    logger.info("Initializing MarkItDown...")
    md = MarkItDown()

    logger.info("Initializing Gemini Embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)

    # Configure Text Splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    # Setup Qdrant connection locally
    logger.info("Connecting to Qdrant...")
    client = QdrantClient(url="http://localhost:6333")

    # Verify collection exists, if not this script assumes it does based on previous logs
    if not client.collection_exists(COLLECTION_NAME):
        logger.error(f"Collection {COLLECTION_NAME} does not exist!")
        return

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )

    for local_path, original_url in FILES_TO_INDEX.items():
        if not os.path.exists(local_path):
            logger.error(f"File not found: {local_path}")
            continue

        logger.info(f"Processing local file: {local_path}")
        try:
            result = md.convert(local_path)
            text_content = result.text_content

            if not text_content or len(text_content.strip()) < 50:
                logger.warning(f"Extracted content is too short or empty for {local_path}")
                continue

            doc = Document(page_content=text_content, metadata={"source": original_url})

            chunks = text_splitter.split_documents([doc])
            logger.info(f"Split into {len(chunks)} chunks.")

            vector_store.add_documents(chunks)
            logger.info(f"Successfully indexed chunks for {original_url}")

        except Exception as e:
            logger.error(f"Failed to process {local_path}: {e}")


if __name__ == "__main__":
    main()

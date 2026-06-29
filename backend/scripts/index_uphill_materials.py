import logging
import os

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from markitdown import MarkItDown
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

LINKS = [
    "https://evokeendurance.com/resources/book-club-training-for-the-uphill-athlete/",
    "https://youtu.be/PP7GqpvIVWY",
    "https://www.youtube.com/watch?v=twzUV-tdMs0",
    "https://youtu.be/1emEMbVnYBo",
    "https://www.youtube.com/watch?v=iIyUMpFAx_A",
    "https://youtu.be/PrWqNDsKnHg",
    "https://youtu.be/CmTg2Wcj1dM",
    "https://youtu.be/UOG5cPN_vkQ",
    "https://youtu.be/jardqEerNKQ",
    "https://youtu.be/htn5zPYg4HA",
    "https://youtu.be/hoz33QXXm4E",
    "https://www.youtube.com/watch?v=_Lpl8B93qsA",
    "https://www.youtube.com/watch?v=_dI12XSrdO0",
    "https://www.youtube.com/watch?v=Ko7Y65hwQQg",
    "https://www.youtube.com/watch?v=MO3X_xQos2o",
    "https://www.youtube.com/watch?v=qFmWQQrC4D0",
    "https://www.youtube.com/watch?v=VoYZks5vuPM",
    "https://www.youtube.com/watch?v=mq6U8Vtm3OA",
    "https://youtu.be/t_Vst_QXYVs",
    "https://youtu.be/yxJi-C33ZzY",
    "https://www.youtube.com/watch?v=Zpju3ggXGXM",
    "https://www.youtube.com/watch?v=sLFZJ-42v7o",
    "https://www.youtube.com/watch?v=phLCY_Stjs0",
    "https://www.youtube.com/watch?v=djn1KRY7510",
    "https://www.youtube.com/watch?v=vAqQPDXtq5k",
    "https://www.youtube.com/watch?v=MyeAXeibgcY",
    "https://www.youtube.com/watch?v=-cb5Q_Tvc0I",
    "https://www.youtube.com/watch?v=PHGIyOuugCk",
    "https://www.youtube.com/watch?v=iZE9IL29U5I",
    "https://www.youtube.com/watch?v=Pb3eTtmMO-Y",
    "https://www.youtube.com/watch?v=h04gDGsh4ww",
    "https://www.youtube.com/watch?v=BjvM0ZPzUFw",
    "https://www.youtube.com/watch?v=gIG9-aM-itg",
    "https://uphillathlete.com/aerobic-training/uphill-athlete-training-zones-heart-rate-calculator/",
    "https://www.runnersworld.com/uk/training/ultra/a65981416/muscular-endurance-fatigue-resistance/",
    "https://bornonthetrail.substack.com/p/should-we-all-be-doing-muscular-endurance-training",
    "https://evokeendurance.com/resources/training-for-mountain-running/",
    "https://evokeendurance.com/resources/zone-2-a-comprehensive-look/",
    "https://evokeendurance.com/resources/pros-and-cons-of-using-rpe-and-heart-rate-in-training/",
    "https://evokeendurance.com/resources/why-even-ultra-runners-need-speed-work/",
    "https://evokeendurance.com/resources/treadmill-season/",
    "https://evokeendurance.com/resources/setting-your-hear-rate-zones/",
    "https://evokeendurance.com/resources/muscular-endurance-all-you-need-to-know/",
    "https://evokeendurance.com/resources/how-training-works/",
]


def main():
    # Load env for GEMINI_API_KEY
    from dotenv import load_dotenv

    load_dotenv()

    md = MarkItDown()

    logger.info("Initializing Google Gemini Embeddings (gemini-embedding-2)...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    logger.info(f"Connecting to Qdrant at {qdrant_url}...")
    client = QdrantClient(url=qdrant_url)

    collection_name = "uphill_athlete_materials"

    # Delete the existing collection if it exists because dimensions are changing
    if client.collection_exists(collection_name):
        logger.info(f"Deleting existing collection {collection_name} to update dimensions...")
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        # gemini-embedding-2 uses 3072 dimensions
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )
    logger.info(f"Created Qdrant collection: {collection_name} with 3072 dimensions")

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for url in set(LINKS):  # Remove duplicates
        logger.info(f"Processing URL: {url}")
        try:
            result = md.convert(url)
            text_content = result.text_content
            if not text_content or len(text_content.strip()) < 50:
                logger.warning(f"Extracted content is too short or empty for {url}")
                continue

            doc = Document(page_content=text_content, metadata={"source": url})

            chunks = text_splitter.split_documents([doc])
            logger.info(f"Split into {len(chunks)} chunks.")

            vector_store.add_documents(chunks)
            logger.info(f"Successfully indexed chunks for {url}")

        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")


if __name__ == "__main__":
    main()

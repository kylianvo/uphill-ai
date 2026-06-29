import json
import logging
import os
import sys

import google.generativeai as genai
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from markitdown import MarkItDown
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# Pydantic Schema for Gemini Structured Output
class NutritionMetadata(BaseModel):
    brand: str = Field(description="The brand of the product (e.g., GU, Maurten, Naak, Tailwind, SiS)")
    name: str = Field(description="The specific name of the product")
    type: str = Field(
        description="The format/type of the product. Must be one of: 'gel', 'chew', 'drink mix', 'bar', 'solid'"
    )
    carbs_g: float = Field(description="Total carbohydrates per serving in grams. Extract as a number.")
    sodium_mg: float = Field(description="Total sodium per serving in milligrams. Extract as a number.")
    caffeine_option: bool = Field(description="True if this product contains caffeine or has a caffeinated variant.")
    summary: str = Field(
        description="A concise 2-sentence summary of the product, including its intended use case and flavors if mentioned."
    )


NUTRITION_URLS = [
    # GU
    "https://www.guenergy.com.au/products/energy-gel",
    "https://www.guenergy.com.au/products/roctane-energy-gel-1",
    "https://www.guenergy.com.au/products/liquid-energy-gel",
    "https://www.guenergy.com.au/products/hydration-tabs",
    "https://www.guenergy.com.au/products/energy-chews",
    # Maurten
    "https://www.maurten.com/products/gel-100-box-us",
    "https://www.maurten.com/products/gel-100-caf-100-box-us",
    "https://www.maurten.com/products/gel-160-us-ca",
    "https://www.maurten.com/products/drink-mix-160-box-us",
    "https://www.maurten.com/products/drink-mix-320-box-us",
    "https://www.maurten.com/products/drink-mix-320-caf-100-us",
    # Naak
    "https://www.naak.com/collections/gels/products/boost-gel-30-neutral",
    "https://www.naak.com/collections/gels/products/ultra-energy-gel-salted-maple",
    "https://www.naak.com/collections/drink-mixes/products/boost-drink-mix-60-neutral-single-serve",
    "https://www.naak.com/collections/drink-mixes/products/ultra-drink-mix-pineapple-single-serve",
    "https://www.naak.com/collections/ultra-energy-purees/products/energy-puree-sweet-potatoes-butternut-squash",
    "https://www.naak.com/collections/energy-waffles/products/salted-caramel-energy-waffle",
    "https://www.naak.com/collections/complete-mix/products/recovery-complete-mix-chocolate-hazelnut-single-serve",
    # SiS
    "https://www.scienceinsport.com.au/go-plus-isotonic-energy-gel-60ml-apple-single/",
    "https://www.scienceinsport.com.au/beta-fuel-gel-60ml-orange-single/",
    "https://www.scienceinsport.com.au/beta-fuel-80-sachet-82g-orange-single/",
    # Tailwind
    "https://www.tailwindnutrition.com.au/products/endurance-fuel",
    "https://www.tailwindnutrition.com.au/products/recovery-mix",
    # Precision
    "https://www.precisionhydration.com/au/en/products/pf-30-gel",
    "https://www.precisionhydration.com/au/en/products/pf-30-caffeine-gel",
    "https://www.precisionhydration.com/au/en/products/pf-90-gel",
    "https://www.precisionhydration.com/au/en/products/carb-electrolyte-drink-mix",
    "https://www.precisionhydration.com/au/en/products/carb-only-drink-mix",
    "https://www.precisionhydration.com/au/en/products/pf-30-chew",
    "https://www.precisionhydration.com/au/en/products/pf-60-chew-bar",
    # Hammer
    "https://www.hammernutrition.com.au/product/hammer-gel/",
    # Bix
    "https://www.bixvitamins.com/en-au/products/the-big-40-gel-1",
    "https://www.bixvitamins.com/en-au/products/bix-gel-strawberry",
    "https://www.bixvitamins.com/en-au/products/performance-fuel-high-carb-drink-mix-copy",
]

COLLECTION_NAME = "uphill_nutrition"
EMBEDDING_MODEL = "models/gemini-embedding-2"


def main():
    if not settings.GEMINI_API_KEY and not settings.GEMINI_API_KEYS:
        logger.error("GEMINI_API_KEY is missing.")
        return

    # Use first key for everything
    api_key = settings.get_next_gemini_key()
    genai.configure(api_key=api_key)

    # Initialize Extraction Model
    model = genai.GenerativeModel("gemini-2.5-flash")

    logger.info("Initializing MarkItDown...")
    md = MarkItDown()

    logger.info("Initializing Embeddings and Qdrant...")
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)

    # Using 'qdrant' as host to run inside docker network, or 'localhost' if running outside.
    # Since we use docker exec, we connect to qdrant:6333
    qdrant_url = "http://qdrant:6333" if os.path.exists("/.dockerenv") else "http://localhost:6333"
    client = QdrantClient(url=qdrant_url)

    if not client.collection_exists(COLLECTION_NAME):
        logger.info(f"Creating collection {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )

    failed_urls = []

    for url in NUTRITION_URLS:
        logger.info(f"Processing URL: {url}")
        try:
            result = md.convert(url)
            text_content = result.text_content

            if not text_content or len(text_content.strip()) < 100:
                logger.warning(f"Extracted content is too short or empty for {url}")
                failed_urls.append((url, "Scraping failed (empty/short content)"))
                continue

            # Extract structured data
            logger.info("Extracting structured metadata via Gemini...")
            prompt = f"Extract the nutrition product details from the following website text. Ensure accurate extraction of carbs (g) and sodium (mg) per serving.\n\nWebsite Text:\n{text_content[:8000]}"

            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json", response_schema=NutritionMetadata, temperature=0.0
                ),
            )

            try:
                metadata_dict = json.loads(response.text)
            except Exception as parse_e:
                logger.error(f"Failed to parse JSON response: {response.text}")
                failed_urls.append((url, f"LLM Parsing failed: {parse_e}"))
                continue

            # Prepare payload
            doc = Document(
                page_content=metadata_dict.get("summary", ""),
                metadata={
                    "source": url,
                    "brand": metadata_dict.get("brand", ""),
                    "name": metadata_dict.get("name", ""),
                    "type": metadata_dict.get("type", ""),
                    "carbs_g": metadata_dict.get("carbs_g", 0.0),
                    "sodium_mg": metadata_dict.get("sodium_mg", 0.0),
                    "caffeine_option": metadata_dict.get("caffeine_option", False),
                    "category": "product",
                },
            )

            # Embed and upsert
            vector_store.add_documents([doc])
            logger.info(f"Successfully indexed: {metadata_dict.get('brand')} - {metadata_dict.get('name')}")

        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            failed_urls.append((url, f"Exception: {e}"))

    print("\n" + "=" * 50)
    if failed_urls:
        print("FAILED URLS:")
        for u, reason in failed_urls:
            print(f"- {u} ({reason})")
    else:
        print("ALL URLS PROCESSED SUCCESSFULLY!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()

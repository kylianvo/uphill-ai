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
class GearMetadata(BaseModel):
    brand: str = Field(
        description="The brand of the shoe (e.g., Hoka, Salomon, Kailas, Asics, Adidas, Nike, Puma, New Balance, On, Mount to Coast, Norda, NNormal)"
    )
    name: str = Field(description="The specific model name of the shoe")
    retail_price: str = Field(description="The retail price of the shoe as a string (e.g., '$180')")
    release: str = Field(description="The release date (month/year) if available, otherwise 'Unknown'")
    terrain: list[str] = Field(
        description="List of suitable terrains (e.g., 'rocky', 'muddy', 'runnable', 'technical', 'road', 'trail')"
    )
    foot_shape: str = Field(description="Foot shape suitability (e.g., 'narrow', 'standard', 'wide', 'roomy toe box')")
    drop: float = Field(description="Heel-to-toe drop in mm. Extract as a number.")
    lug_depth: float = Field(description="Lug depth in mm. If road shoe or unknown, use 0.0.")
    foam: str = Field(description="Midsole foam material or technology (e.g., 'PEBA', 'EVA', 'ZoomX')")
    community_score: float = Field(
        description="Overall rating or community score out of 100 (or convert out of 10). Extract as a number out of 100 if possible, or fallback to 0.0."
    )
    pros: list[str] = Field(description="List of 3-5 pros or positive aspects of the shoe")
    cons: list[str] = Field(description="List of 3-5 cons or negative aspects of the shoe")
    carbon_plate: bool = Field(
        description="True if the shoe contains a carbon plate, carbon rods, or similar stiffening element."
    )
    summary: str = Field(
        description="A concise 3-sentence summary of the shoe, its best use cases, and overall feel (e.g., plush, responsive)."
    )


GEAR_URLS = [
    # Hoka
    "https://runrepeat.com/hoka-tecton-x-3",
    "https://bettertrail.com/outdoor-gear/hoka-speedgoat-7-trail-running-shoe-review",
    "https://runrepeat.com/hoka-mafate-5",
    "https://runrepeat.com/hoka-mach-7",
    "https://runrepeat.com/hoka-mach-x-3",
    "https://runrepeat.com/hoka-rocket-x-3",
    "https://runrepeat.com/hoka-cielo-x-1-3-0",
    "https://runrepeat.com/hoka-clifton-10",
    "https://runrepeat.com/hoka-bondi-9",
    "https://runrepeat.com/hoka-arahi-8",
    # Salomon
    "https://runrepeat.com/salomon-s-lab-genesis",
    "https://runrepeat.com/salomon-genesis",
    "https://runrepeat.com/salomon-s-lab-pulsar-4",
    "https://www.roadtrailrun.com/2026/05/salomon-slab-ultra-glide-2-multi-tester.html",
    "https://runrepeat.com/salomon-ultra-glide-4",
    "https://runrepeat.com/salomon-speedcross-6",
    "https://runrepeat.com/salomon-aero-glide-4",
    "https://www.roadtrailrun.com/2025/07/salomon-aero-blaze-3-multi-tester.html",
    "https://runrepeat.com/salomon-aero-glide-4-grvl",
    "https://believeintherun.com/shoe-reviews/salomon-aero-blaze-3-grvl-review/",
    "https://believeintherun.com/shoe-reviews/salomon-s-lab-phantasm-3-review/",
    # Kailas
    "https://believeintherun.com/shoe-reviews/kailas-fuga-ex330-review/",
    "https://runrepeat.com/kailas-fuga-ex-pro",
    # Asics
    "https://runrepeat.com/asics-metaspeed-sky-tokyo",
    "https://runrepeat.com/asics-metaspeed-edge-tokyo",
    "https://runrepeat.com/asics-superblast-3",
    "https://runrepeat.com/asics-novablast-5",
    # Adidas
    "https://believeintherun.com/shoe-reviews/adidas-terrex-agravic-speed-ultra-2-review/",
    "https://believeintherun.com/shoe-reviews/adidas-terrex-agravic-tt-review/",
    "https://believeintherun.com/shoe-reviews/adidas-terrex-agravic-speed-2-review/",
    "https://believeintherun.com/shoe-reviews/adidas-adizero-boston-13-review/",
    "https://believeintherun.com/shoe-reviews/adidas-adizero-evo-sl-review/",
    "https://believeintherun.com/shoe-reviews/adidas-hyperboost-edge-review/",
    "https://believeintherun.com/shoe-reviews/adidas-adizero-adios-pro-4-review/",
    # Nike
    "https://runrepeat.com/nike-acg-ultrafly-trail",
    "https://runrepeat.com/nike-alphafly-3",
    "https://runrepeat.com/nike-vomero-18",
    "https://runrepeat.com/nike-vaporfly-4",
    "https://runrepeat.com/nike-vomero-plus",
    "https://runrepeat.com/nike-zoom-fly-6",
    "https://runrepeat.com/nike-pegasus-42",
    # Puma
    "https://believeintherun.com/shoe-reviews/puma-deviate-nitro-pure-review/",
    "https://believeintherun.com/shoe-reviews/puma-deviate-nitro-elite-4-review/",
    "https://believeintherun.com/shoe-reviews/puma-deviate-nitro-4-review/",
    "https://believeintherun.com/shoe-reviews/puma-velocity-nitro-4-review/",
    "https://believeintherun.com/shoe-reviews/puma-fast-r-nitro-elite-3-review/",
    # New Balance
    "https://believeintherun.com/shoe-reviews/new-balance-rebel-v5-review/",
    # On
    "https://believeintherun.com/shoe-reviews/on-cloudultra-3-review/",
    "https://believeintherun.com/shoe-reviews/on-cloudultra-pro-review/",
    "https://runrepeat.com/on-cloudmonster-3",
    "https://runrepeat.com/on-cloudmonster-3-hyper",
    "https://runrepeat.com/on-cloudboom-strike",
    # Mount to Coast
    "https://believeintherun.com/shoe-reviews/mount-to-coast-t1-review/",
    "https://believeintherun.com/shoe-reviews/mount-to-coast-h1-review/",
    "https://believeintherun.com/shoe-reviews/mount-to-coast-c1-review/",
    # Norda
    "https://believeintherun.com/shoe-reviews/norda-001a-review/",
    "https://believeintherun.com/shoe-reviews/norda-005-review/",
    # NNormal
    "https://www.outdoorgearlab.com/reviews/shoes-and-boots/trail-running-shoes-men/nnormal-kjerag-02",
    "https://www.outdoorgearlab.com/reviews/shoes-and-boots/trail-running-shoes-men/nnormal-tomir-2-0",
    "https://www.roadtrailrun.com/2026/04/nnormal-cadi-multi-tester-review-5.html",
]

COLLECTION_NAME = "uphill_gear"
EMBEDDING_MODEL = "models/gemini-embedding-2"


def main():
    if not settings.GEMINI_API_KEY and not settings.GEMINI_API_KEYS:
        logger.error("GEMINI_API_KEY is missing.")
        return

    api_key = settings.get_next_gemini_key()
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-2.5-flash")

    logger.info("Initializing MarkItDown...")
    md = MarkItDown()

    logger.info("Initializing Embeddings and Qdrant...")
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)

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

    for url in GEAR_URLS:
        logger.info(f"Processing URL: {url}")
        try:
            result = md.convert(url)
            text_content = result.text_content

            if not text_content or len(text_content.strip()) < 100:
                logger.warning(f"Extracted content is too short or empty for {url}")
                failed_urls.append((url, "Scraping failed (empty/short content)"))
                continue

            logger.info("Extracting structured metadata via Gemini...")
            prompt = f"Extract the shoe details from the following review website text. Find the drop (mm), lug depth (mm, if trail), foams used, carbon plate presence, pros, and cons.\n\nWebsite Text:\n{text_content[:8000]}"

            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json", response_schema=GearMetadata, temperature=0.0
                ),
            )

            try:
                metadata_dict = json.loads(response.text)
            except Exception as parse_e:
                logger.error(f"Failed to parse JSON response: {response.text}")
                failed_urls.append((url, f"LLM Parsing failed: {parse_e}"))
                continue

            summary_text = metadata_dict.get("summary", "")
            pros_text = "Pros: " + ", ".join(metadata_dict.get("pros", []))
            cons_text = "Cons: " + ", ".join(metadata_dict.get("cons", []))
            page_content = f"{summary_text}\n\n{pros_text}\n{cons_text}"

            doc = Document(
                page_content=page_content,
                metadata={
                    "source": url,
                    "brand": metadata_dict.get("brand", ""),
                    "name": metadata_dict.get("name", ""),
                    "retail_price": metadata_dict.get("retail_price", ""),
                    "release": metadata_dict.get("release", ""),
                    "terrain": metadata_dict.get("terrain", []),
                    "foot_shape": metadata_dict.get("foot_shape", ""),
                    "drop": metadata_dict.get("drop", 0.0),
                    "lug_depth": metadata_dict.get("lug_depth", 0.0),
                    "foam": metadata_dict.get("foam", ""),
                    "community_score": metadata_dict.get("community_score", 0.0),
                    "carbon_plate": metadata_dict.get("carbon_plate", False),
                    "category": "shoe_review",
                },
            )

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

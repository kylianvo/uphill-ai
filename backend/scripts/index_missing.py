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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class NutritionMetadata(BaseModel):
    brand: str = Field(description="The brand of the product")
    name: str = Field(description="The specific name of the product")
    type: str = Field(
        description="The format/type of the product. Must be one of: 'gel', 'chew', 'drink mix', 'bar', 'solid'"
    )
    carbs_g: float = Field(description="Total carbohydrates per serving in grams. Extract as a number.")
    sodium_mg: float = Field(description="Total sodium per serving in milligrams. Extract as a number.")
    caffeine_option: bool = Field(description="True if this product contains caffeine or has a caffeinated variant.")
    summary: str = Field(description="A concise 2-sentence summary of the product.")


class GearMetadata(BaseModel):
    brand: str = Field(description="The brand of the shoe")
    name: str = Field(description="The specific model name of the shoe")
    retail_price: str = Field(description="The retail price")
    release: str = Field(description="The release date")
    terrain: list[str] = Field(description="List of suitable terrains")
    foot_shape: str = Field(description="Foot shape suitability")
    drop: float = Field(description="Heel-to-toe drop in mm")
    lug_depth: float = Field(description="Lug depth in mm")
    foam: str = Field(description="Midsole foam material")
    community_score: float = Field(description="Overall rating out of 100")
    pros: list[str] = Field(description="List of 3-5 pros")
    cons: list[str] = Field(description="List of 3-5 cons")
    carbon_plate: bool = Field(description="True if the shoe contains a carbon plate")
    summary: str = Field(description="A concise 3-sentence summary")


def main():
    api_key = settings.get_next_gemini_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", google_api_key=api_key)

    qdrant_url = "http://qdrant:6333" if os.path.exists("/.dockerenv") else "http://localhost:6333"
    client = QdrantClient(url=qdrant_url)

    # 1. GU Hydration Drink Tabs
    gu_text = """
GU Hydration Drink Tabs provide a boost to your water by supplementing it with electrolytes for improved performance and recovery. Each drink tab contains just 10 calories, in addition to 320 milligrams of sodium and 55 milligrams of potassium to help maintain fluid balance and delay fatigue by replacing electrolytes depleted during exercise.

Performance Fuel
90 calories per serving to fuel your activity
22 grams of carbohydrates for quick and sustained energy
40 milligrams of sodium to replace electrolytes lost in sweat
400 milligrams of amino acids to support muscle performance
Available with caffeine in select flavors for added focus
    """

    logger.info("Extracting structured metadata for GU Drink Tabs...")
    gu_response = model.generate_content(
        f"Extract the nutrition product details from the following text.\n\nText:\n{gu_text}",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", response_schema=NutritionMetadata, temperature=0.0
        ),
    )

    gu_meta = json.loads(gu_response.text)

    gu_doc = Document(
        page_content=gu_meta.get("summary", "Hydration and performance fuel drink mix."),
        metadata={
            "source": "https://www.guenergy.com.au/products/hydration-tabs",
            "brand": gu_meta.get("brand", "GU"),
            "name": gu_meta.get("name", "Hydration Drink Tabs"),
            "type": gu_meta.get("type", "drink mix"),
            "carbs_g": gu_meta.get("carbs_g", 22.0),
            "sodium_mg": gu_meta.get("sodium_mg", 320.0),
            "caffeine_option": gu_meta.get("caffeine_option", True),
            "category": "product",
        },
    )

    store_nutrition = QdrantVectorStore(client=client, collection_name="uphill_nutrition", embedding=embeddings)
    store_nutrition.add_documents([gu_doc])
    logger.info(f"Successfully indexed: {gu_meta.get('brand')} - {gu_meta.get('name')}")

    # 2. Hoka Speedgoat 7
    hoka_url = "https://believeintherun.com/shoe-reviews/hoka-speedgoat-7-review/"
    logger.info("Initializing MarkItDown for Hoka Speedgoat 7...")
    md = MarkItDown()
    result = md.convert(hoka_url)
    hoka_text = result.text_content

    logger.info("Extracting structured metadata for Speedgoat 7 via Gemini...")
    hoka_response = model.generate_content(
        f"Extract the shoe details from the following review website text.\n\nWebsite Text:\n{hoka_text[:8000]}",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", response_schema=GearMetadata, temperature=0.0
        ),
    )

    hoka_meta = json.loads(hoka_response.text)
    summary_text = hoka_meta.get("summary", "")
    pros_text = "Pros: " + ", ".join(hoka_meta.get("pros", []))
    cons_text = "Cons: " + ", ".join(hoka_meta.get("cons", []))
    page_content = f"{summary_text}\n\n{pros_text}\n{cons_text}"

    hoka_doc = Document(
        page_content=page_content,
        metadata={
            "source": hoka_url,
            "brand": hoka_meta.get("brand", ""),
            "name": hoka_meta.get("name", ""),
            "retail_price": hoka_meta.get("retail_price", ""),
            "release": hoka_meta.get("release", ""),
            "terrain": hoka_meta.get("terrain", []),
            "foot_shape": hoka_meta.get("foot_shape", ""),
            "drop": hoka_meta.get("drop", 0.0),
            "lug_depth": hoka_meta.get("lug_depth", 0.0),
            "foam": hoka_meta.get("foam", ""),
            "community_score": hoka_meta.get("community_score", 0.0),
            "carbon_plate": hoka_meta.get("carbon_plate", False),
            "category": "shoe_review",
        },
    )

    store_gear = QdrantVectorStore(client=client, collection_name="uphill_gear", embedding=embeddings)
    store_gear.add_documents([hoka_doc])
    logger.info(f"Successfully indexed: {hoka_meta.get('brand')} - {hoka_meta.get('name')}")

    print("\nALL MISSING ITEMS INDEXED SUCCESSFULLY!\n")


if __name__ == "__main__":
    main()

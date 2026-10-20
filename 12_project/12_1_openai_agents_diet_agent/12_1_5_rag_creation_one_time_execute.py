# Run this code only once to create the ChromaDB collection
from typing import Dict
import chromadb
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def prepare_nutrition_documents(csv_path: str) -> Dict:
    """
    Convert nutrition CSV into ChromaDB-ready documents.
    Each food item becomes a searchable document.
    """
    df = pd.read_csv(csv_path)

    documents = []
    metadatas = []
    ids = []

    for index, row in df.iterrows():
        # Safe string cleanup
        cals = str(row["Cals_per100grams"]).replace(" cal", "")
        kj = str(row["KJ_per100grams"]).replace(" kJ", "")

        document_text = f"""
Food: {row['FoodItem']}
Category: {row['FoodCategory']}
Nutritional Information:
- Calories: {cals} per 100g
- Energy: {kj} kJ per 100g
- Serving size reference: {row['per100grams']}

This is a {row['FoodCategory'].lower()} food item that provides {cals} calories per 100 grams.
""".strip()

        metadata = {
            "food_item": row["FoodItem"].lower(),
            "food_category": row["FoodCategory"].lower(),
            "calories_per_100g": float(cals) if cals.replace(".", "").isdigit() else 0.0,
            "kj_per_100g": float(kj) if kj.replace(".", "").isdigit() else 0.0,
            "serving_info": row["per100grams"],
            "keywords": f"{row['FoodItem']} {row['FoodCategory']}".lower().replace(" ", "_"),
        }

        documents.append(document_text)
        metadatas.append(metadata)
        ids.append(f"food_{index}")

    return {"documents": documents, "metadatas": metadatas, "ids": ids}


def setup_nutrition_chromadb(csv_path: str, collection_name: str = "nutrition_db"):
    client = chromadb.PersistentClient(
        path=os.path.join(BASE_DIR, "data", "chroma")
    )

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Nutrition database with calorie and food information"},
    )

    data = prepare_nutrition_documents(csv_path)

    collection.add(
        documents=data["documents"],
        metadatas=data["metadatas"],
        ids=data["ids"],
    )

    print(f"Added {len(data['documents'])} food items to '{collection_name}'")
    return collection


# ---- BUILD DB ----
collection = setup_nutrition_chromadb(
    os.path.join(BASE_DIR, "data", "calories.csv"),
    "nutrition_db",
)

# ---- QUERY DB ----
chroma_client = chromadb.PersistentClient(
    path=os.path.join(BASE_DIR, "data", "chroma")
)

nutrition_db = chroma_client.get_collection(name="nutrition_db")

results = nutrition_db.query(query_texts=["banana"], n_results=3)

for i, doc in enumerate(results["documents"][0]):
    print(results["metadatas"][0][i])
    print(doc)
    print()

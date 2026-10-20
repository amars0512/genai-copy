import random
import chromadb
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "data", "chroma")


def setup_chromadb(file_path, collection_name="nutrition_qna", sample_pct=0.05):
    """Load Q&A pairs into ChromaDB."""
    # Read and sample pairs
    with open(file_path, encoding="utf-8") as f:
        pairs = [p.strip() for p in f.read().split("\n\n") if p.strip()]
    
    sample = random.sample(pairs, max(1, int(len(pairs) * sample_pct)))
    print(f"Loaded {len(sample)} of {len(pairs)} pairs")
    
    # Parse Q&A
    qa_list = []
    for i, pair in enumerate(sample):
        lines = pair.split("\n")
        q = next((l[9:].strip() for l in lines if l.startswith("Question:")), "")
        a = next((l[7:].strip() for l in lines if l.startswith("Answer:")), "")
        if q and a:
            qa_list.append((f"Question: {q}\nAnswer: {a}", {"q": q, "a": a}, f"qa_{i}"))
    
    # Store in ChromaDB
    client = chromadb.PersistentClient(DB_PATH)
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    coll = client.create_collection(collection_name)
    coll.add(
        documents=[qa[0] for qa in qa_list],
        metadatas=[qa[1] for qa in qa_list],
        ids=[qa[2] for qa in qa_list]
    )
    print(f"Added to '{collection_name}'")
    return coll


# Usage example
if __name__ == "__main__":
    # Setup (run once)
    setup_chromadb(os.path.join(BASE_DIR, "data", "questions_output.txt"))
    
    # Query
    client = chromadb.PersistentClient(DB_PATH)
    coll = client.get_collection("nutrition_qna")
    
    print(f"Total Q&A pairs: {coll.count()}\n")
    
    results = coll.query(query_texts=["pregnancy"], n_results=3)
    
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        print(f"Result {i+1}:")
        print(f"Q: {meta['q']}")
        print(f"A: {meta['a']}\n")
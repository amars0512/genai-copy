# pip install sentence-transformers, sklearn
# Embeddings at four levels of context - word, sentence, paragraph, chapter - on one topic (banking).
# An embedding represents meaning in context, not the amount of text.
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# -----------------------------
# 1. One topic, four levels
# -----------------------------
word = "bank"

sentence = "I deposited money at the bank."

paragraph = (
    "I deposited my salary into my bank account. I then transferred some money to a friend "
    "and checked my remaining balance using the mobile banking application."
)

# A short stand-in for a chapter, kept as sections (chunks).
# A real chapter runs to thousands of tokens and must be chunked like this.
chapter_sections = [
    "Introduction to Digital Banking. A bank account lets customers keep money safely, "
    "deposit cash or cheques and withdraw funds whenever they need them.",
    "Fund transfers move money between accounts. Customers can send money to friends, pay bills "
    "and receive their salary directly into their account.",
    "Banks pay interest on savings and charge interest on loans. Home loans, car loans and "
    "personal loans each have different interest rates and repayment periods.",
    "Digital payments such as UPI, debit cards and net banking let customers pay instantly "
    "from a mobile phone or computer without visiting a branch.",
    "Fraud prevention protects customers. Never share your OTP or PIN, and report any "
    "suspicious transaction to the bank immediately.",
    "Mobile banking applications let customers check their balance, view statements, "
    "transfer funds and manage cards from anywhere.",
]
chapter = " ".join(chapter_sections)

# -----------------------------
# 2. Why chapters need chunking
# -----------------------------
print(f"Model input limit: {model.max_seq_length} tokens (longer text is silently cut off)\n")
for name, text in [("Word", word), ("Sentence", sentence), ("Paragraph", paragraph), ("Chapter", chapter)]:
    tokens = len(model.tokenizer.tokenize(text))
    print(f"{name:10s}: {tokens:4d} tokens")
print("\nOur mini-chapter fits, but a real one (thousands of tokens) would not,")
print("so we embed it section by section and average the vectors.")

# -----------------------------
# 3. Create the four embeddings
# -----------------------------
word_vec, sentence_vec, paragraph_vec = model.encode([word, sentence, paragraph])

# Chapter: embed each section, then average them into one vector
section_vecs = model.encode(chapter_sections)
chapter_vec = np.mean(section_vecs, axis=0)

labels = ["Word", "Sentence", "Paragraph", "Chapter"]
embeddings = np.array([word_vec, sentence_vec, paragraph_vec, chapter_vec])
print(f"\nEvery level becomes the same size vector: {embeddings.shape}")

# -----------------------------
# 4. Cosine similarity between the four levels
# -----------------------------
cos_sim = cosine_similarity(embeddings)

print("\n=== COSINE SIMILARITY ===\n")
print(" " * 11 + "".join(f"{label:>11s}" for label in labels))
for i, label in enumerate(labels):
    print(f"{label:11s}" + "".join(f"{cos_sim[i][j]:11.3f}" for j in range(len(labels))))

# -----------------------------
# 5. Context changes the meaning of "bank"
# -----------------------------
river_sentence = "We sat on the bank of the river and watched the boats."
river_vec = model.encode(river_sentence)

print("\n=== WHICH 'BANK'? ===\n")
print(f"'bank'       vs money sentence : {cosine_similarity([word_vec], [sentence_vec])[0][0]:.3f}")
print(f"'bank'       vs river sentence : {cosine_similarity([word_vec], [river_vec])[0][0]:.3f}")
print(f"money chapter vs river sentence: {cosine_similarity([chapter_vec], [river_vec])[0][0]:.3f}")

# -----------------------------
# 6. One chapter vector vs its chunks
# -----------------------------
question = "What should I do if I see a suspicious transaction?"
question_vec = model.encode(question)

print(f"\n=== QUESTION: {question} ===\n")
print(f"vs whole-chapter vector: {cosine_similarity([question_vec], [chapter_vec])[0][0]:.3f}")
scores = cosine_similarity([question_vec], section_vecs)[0]
for score, section in sorted(zip(scores, chapter_sections), reverse=True)[:2]:
    print(f"vs section             : {score:.3f}  {section[:60]}...")

print("\nThe chapter vector captures the overall topic; the specific answer lives in one chunk.")
print("That is why RAG systems store chunk embeddings, not just one per chapter.")

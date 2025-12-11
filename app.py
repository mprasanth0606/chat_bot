
# pip install ollama langchain-ollama pypdf faiss-cpu langchain-community
import ollama
from pypdf import PdfReader
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

# -------------------------------
# 1. LOAD PDF
# -------------------------------
def load_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# -------------------------------
# 2. SPLIT PDF INTO CHUNKS
# -------------------------------
def chunk_text(text, chunk_size=500, chunk_overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

# -------------------------------
# 3. BUILD VECTOR STORE
# -------------------------------
def build_vector_store(chunks):
    embed_model = OllamaEmbeddings(model="nomic-embed-text")  # must be pulled first
    vectordb = FAISS.from_texts(chunks, embed_model)
    return vectordb

# -------------------------------
# 4. RAG CHAT FUNCTION
# -------------------------------

def rag_chat(query, vectordb, llm_model="qwen3:4b"):
    results = vectordb.similarity_search(query, k=3)
    context = "\n\n".join([r.page_content for r in results])

    prompt = f"""
You are an Time sheet assistant. Answer the question based ONLY on the context below.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""
    # Latest Ollama SDK usage
    response = ollama.chat(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}]
    )
    print(response)
    # Extract the generated text
    answer_text = response.message.content
    return answer_text
# -------------------------------
# 5. MAIN WORKFLOW
# -------------------------------
pdf_path = "data/timesheet_user_manual.pdf"

print("Loading PDF...")
text = load_pdf_text(pdf_path)

print("Splitting PDF into chunks...")
chunks = chunk_text(text)

print("Building FAISS vector store...")
vectordb = build_vector_store(chunks)

print("RAG system ready! Ask your  questions.\n")

# -------------------------------
# 6. CHAT LOOP
# -------------------------------
# while True:
#     query = input("Ask your  question (or type 'exit'): ")
#     if query.lower() == "exit":
#         print("Exiting...")
#         break

#     # Get AI answer
#     answer = rag_chat(query, vectordb, llm_model="qwen3:4b")

#     # Print only question and answer
#     print("\nQuestion:", query)
#     print("Answer:", answer)
#     print("-" * 50)

    # -------------------------------
# RAG CHAT FUNCTION FOR API
# -------------------------------

def get_rag_answer(query, vectordb, llm_model="qwen3:4b"):
    """
    Takes a question string and returns only the AI-generated answer text.
    Ensures no extra text, no printing, no context — just the plain answer.
    """
    # Retrieve top relevant documents
    results = vectordb.similarity_search(query, k=3)
    context = "\n\n".join([r.page_content for r in results])

    #  Prompt the model to respond with ONLY the answer
    prompt = f"""
You are a Timesheet assistant. Answer the question using ONLY the context below.
Do NOT add explanations, preambles, or extra text. Provide the plain answer.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""
    response = ollama.chat(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}]
    )

    #  Return just the answer
    return response.message.content.strip()

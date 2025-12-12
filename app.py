
# pip install faiss-cpu langchain-community
from pypdf import PdfReader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
#pip install google-generativeai
import google.generativeai as genai
  
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
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = FAISS.from_texts(chunks, embed_model)
    return vectordb

# -------------------------------
#  MAIN WORKFLOW
# -------------------------------
pdf_path = "data/timesheet_user_manual.pdf"

print("Loading PDF...")
text = load_pdf_text(pdf_path)

print("Splitting PDF into chunks...")
chunks = chunk_text(text)

print("Building FAISS vector store...")
vectordb = build_vector_store(chunks)

print("RAG system ready! Ask your  questions.\n")

#     -------------------------------
# RAG CHAT FUNCTION FOR API
# -------------------------------
  # Set  API key
genai.configure(api_key="AIzaSyA3bjzMIGNx32xmNkD84qwMv5PkZqgqZWo")
def get_rag_answer(query, vectordb, llm_model="gemini-2.5-flash"):
    results = vectordb.similarity_search(query, k=3)
    context = "\n\n".join([r.page_content for r in results])

    prompt = f"""
You are a Time Sheet assistant.
Answer the question based ONLY on the context below.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

    model = genai.GenerativeModel(llm_model)
    response = model.generate_content(prompt)
    return response.text

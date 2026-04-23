from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from backend.config import CHROMA_DIR, EMBED_MODEL, TOP_K

# -------------------
# 1. Embedding model
# -------------------
embedding_model = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": "cpu"},
)

# -------------------
# 2. Vectorstore
# -------------------
vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embedding_model,
)

# -------------------
# 3. Retriever
# -------------------
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": TOP_K, "fetch_k": 20, "lambda_mult": 0.5},
)

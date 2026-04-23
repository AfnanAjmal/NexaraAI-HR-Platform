from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from backend.database.chroma import retriever
from backend.config import GROQ_API_KEY, MODEL_NAME


# -------------------
# 1. LLM
# -------------------
llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0.7)


# -------------------
# 2. Prompt
# -------------------
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful AI assistant for NexaraAI.\n"
     "Use ONLY the provided context to answer the question.\n"
     "If the answer is not in the context, say: I could not find the answer in the document.\n"
     "Be concise and professional."),
    ("human", "Question: {question}\n\nContext:\n{context}"),
])


# -------------------
# 3. Pipeline
# -------------------
def rag_pipeline(query: str) -> str:
    docs    = retriever.invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)
    prompt  = prompt_template.invoke({"question": query, "context": context})
    return llm.invoke(prompt).content

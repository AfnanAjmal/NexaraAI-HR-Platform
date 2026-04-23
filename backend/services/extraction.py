from langchain_groq import ChatGroq

from backend.models.schemas import ResumeInfo, JDInfo
from backend.config import GROQ_API_KEY, MODEL_NAME


# -------------------
# 1. LLM
# -------------------
llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0)

resume_extractor = llm.with_structured_output(ResumeInfo)
jd_extractor     = llm.with_structured_output(JDInfo)


# -------------------
# 2. Extractors
# -------------------
def extract_resume(resume_text: str) -> ResumeInfo:
    prompt = f"Extract structured information from the following resume:\n\n{resume_text}"
    return resume_extractor.invoke(prompt)


def extract_jd(jd_text: str) -> JDInfo:
    prompt = f"Extract structured information from the following job description:\n\n{jd_text}"
    return jd_extractor.invoke(prompt)


# -------------------
# 3. PDF text extraction
# -------------------
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    import fitz  # PyMuPDF
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text.strip()

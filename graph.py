import os
from dotenv import load_dotenv

load_dotenv()

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from backend.graph.chat_graph      import chat_app
from backend.graph.interview_graph import interview_app

# -------------------
# 1. Chat graph
# -------------------
print("Saving chat_graph.png ...")
chat_png = chat_app.get_graph().draw_mermaid_png()
with open("chat_graph.png", "wb") as f:
    f.write(chat_png)
print("✅ chat_graph.png saved")

# -------------------
# 2. Interview graph
# -------------------
print("Saving interview_graph.png ...")
interview_png = interview_app.get_graph().draw_mermaid_png()
with open("interview_graph.png", "wb") as f:
    f.write(interview_png)
print("✅ interview_graph.png saved")

print("\nDone! Open chat_graph.png and interview_graph.png to view.")

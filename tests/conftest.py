import os

# Keep the test suite offline and deterministic: an empty key makes LLMService use its fallback.
# load_dotenv() never overrides variables that are already set, so backend/.env is ignored here.
os.environ["GROQ_API_KEY"] = ""

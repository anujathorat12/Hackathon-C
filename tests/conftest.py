import os

# Keep the test suite offline and deterministic: an empty key makes LLMService use its fallback.
# load_dotenv() never overrides variables that are already set, so backend/.env is ignored here.
os.environ["GROQ_API_KEY"] = ""
# Likewise an empty MongoDB URI keeps tests on the in-memory store instead of a real database.
os.environ["MONGODB_URI"] = ""

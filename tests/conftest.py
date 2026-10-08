import os
import sys

# Ensure backend directory is in python module search path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Keep the test suite offline and deterministic: empty keys make LLMService use its fallback.
# load_dotenv() never overrides variables that are already set, so backend/.env is ignored here.
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["MISTRAL_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
# Likewise an empty MongoDB URI keeps tests on the in-memory store instead of a real database.
os.environ["MONGODB_URI"] = ""

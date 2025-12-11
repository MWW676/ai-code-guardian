from dotenv import load_dotenv
from providers.gemini_client import GeminiClient

load_dotenv()
content = "Explain how AI works in a few words"
provider = GeminiClient()
resp = provider.analyze_diff(contents=content)
print(f"Check in local run: \n{resp}")
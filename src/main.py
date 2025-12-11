import pathlib
from dotenv import load_dotenv
from providers.gemini_client import GeminiClient

load_dotenv()
current_dir = pathlib.Path(__file__).parent
file_path = current_dir.parent / 'test_data' / 'test_diff.txt'
try:
    diff_data = file_path.read_text(encoding='utf-8')
except FileNotFoundError:
    diff_data = "No diff found."

provider = GeminiClient()
resp = provider.analyze_diff(contents=diff_data)
if resp.get('status') != 'ERROR':
    print(f"Check in local run: \n{resp}")
else:
    print(f"Error during execution: {resp.get('error')}")

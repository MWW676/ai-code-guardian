import sys
import logging
import pathlib
from dotenv import load_dotenv
from providers.gemini_client import GeminiClient
from providers.s3_client import S3Uploader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
main_logger = logging.getLogger(__name__)

def ai_code_guardian():
    load_dotenv()
    current_dir = pathlib.Path(__file__).parent
    file_path = current_dir.parent / 'test_data' / 'test_diff.txt'
    try:
        diff_data = file_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        diff_data = "No diff found."

    provider = GeminiClient()
    resp = provider.analyze_diff(contents=diff_data)

    if resp.get('status') not in ['ERROR', 'SKIPPED']:
        print(f"Check in local run: \n{resp}\n")
        uploader = S3Uploader()
        upload_status = uploader.save_report(resp)
        assert upload_status is True
    else:
        print(f"Execution errored or skipped: {resp}")

if __name__ == "__main__":
    ai_code_guardian()

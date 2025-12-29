import json
import logging
from src.providers.gemini_client import GeminiClient
from src.providers.s3_client import S3Uploader
from src.providers.github_client import GithubClient
from src.utils.markdown_utils import format_report_to_markdown
from src.utils.ssm_config_paths import *
import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ssm_client = boto3.client('ssm')

def get_configs():
    try:
        names = [
            GEMINI_API_KEY,
            GITHUB_WEB_SECRET,
            GITHUB_API_KEY,
            S3_BUCKET_NAME
        ]
        resp = ssm_client.get_parameters(Names=names, WithDecryption=True)
        return {p['Name']: p['Value'] for p in resp['Parameters']}

    except Exception as e:
        logger.error(f"Failed to load ssm configs: {e}")
        raise Exception

def lambda_handler(event, context):
    # print message for debug ease
    logger.info(f"Received message: {json.dumps(event)}")
    configs = get_configs()

    for record in event['Records']:
        # Retrieve repo and pr_number
        body = json.loads(record['body'])
        repo_full_name = body.get('repo_full_name')
        pull_request_number = body.get('pr_number')
        if not repo_full_name or not pull_request_number:
            logger.error("Missing repo name or PR number in message.")
            raise Exception

        # Fetch diff and perform analysis
        try:
            # Call Github API to fetch diff
            logger.info(f"Fetching Git diff for {repo_full_name} PR #{pull_request_number}...")
            github_client = GithubClient(api_key=configs.get(GITHUB_API_KEY))
            diff_data = github_client.get_diff(repo_full_name=repo_full_name, pr_number=pull_request_number)
            if diff_data == 'ERROR':
                logger.error("Failed to fetch diff from Github.")
                raise Exception

            # Call Gemini API to perform analysis
            logger.info("Starting AI analysis ...")
            provider = GeminiClient(api_key=configs.get(GEMINI_API_KEY))
            resp = provider.analyze_diff(contents=diff_data)

            if resp.get('status') == 'SKIPPED':
                logger.warning(f'Analysis skipped due to query quota exceeded: {resp}')
                return 0

            elif resp.get('status') == 'ERROR':
                logger.error(f"Error during AI analysis: {resp}")
                raise Exception

            # Generate report
            markdown_report = format_report_to_markdown(report_data=resp)

            # Call Github API to post report as PR comment
            logger.info(f"Posting comment for {repo_full_name} PR#{pull_request_number}...")
            post_success = github_client.post_comment(repo_full_name=repo_full_name, pr_number=pull_request_number, pr_comments=markdown_report)
            if not post_success:
                logger.error("⚠️ Failed to post comment to GitHub, but proceeding to S3 upload.")

            # Store report results
            uploader = S3Uploader(bucket_name=configs.get(S3_BUCKET_NAME))
            upload_success = uploader.save_report(resp)

            execution_result = {
                'message': 'Analysis complete.',
                's3_upload': 'Success' if upload_success else 'Failed',
                'github_comment': 'Success' if post_success else 'Failed',
                'data': resp
            }
            logger.info(f"Consumer execution completed, results: {json.dumps(execution_result)}")

        except Exception as e:
            logger.error(f"Critical execution error:{str(e)}", exc_info=True)
            raise Exception

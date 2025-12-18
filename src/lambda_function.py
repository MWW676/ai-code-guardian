import json
import logging
from src.providers.gemini_client import GeminiClient
from src.providers.s3_client import S3Uploader
from src.providers.github_client import GithubClient
from src.utils.markdown_utils import format_report_to_markdown

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # print event for debug ease
    logger.info(f"Received event: {json.dumps(event)}")

    # Filter PR event by header
    headers = event.get('headers', {})
    github_event = headers.get('X-GitHub-Event') or headers.get('x-github-event')

    if github_event == 'ping':
        logger.info("Received Github ping event, return 200.")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Pong!'})}

    # Process event payload
    event_body = event.get('body')
    if not event_body:
        logger.error("No event body provided.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing event body.'})
        }
    payload = json.loads(event_body) if isinstance(event_body, str) else event_body

    # Filter PR action for analysis
    action = payload.get('action')
    if action not in ['opened', 'synchronize']:
        logger.info(f"Ignoring action {action}. Only open and synchronize actions are supported.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Action {action} ignored.'})
        }

    repo_full_name = payload.get('repository', {}).get('full_name')
    pull_request_number = payload.get('pull_request', {}).get('number')
    if not repo_full_name or not pull_request_number:
        logger.error("Missing repo name or PR number metadata.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Bad payload.'})
        }

    try:
        # Call Github API to retrieve git diff
        logger.info(f"Fetching Git diff for {repo_full_name} PR#{pull_request_number}...")
        github_client = GithubClient()
        diff_data = github_client.get_diff(repo_full_name=repo_full_name, pr_number=pull_request_number)
        if diff_data == 'ERROR':
            return {
                'statusCode': 502,
                'body': json.dumps({'error': "Failed to fetch diff from Github."})
            }

        # Call Gemini API to perform analysis on git diff
        logger.info("Starting AI analysis ...")
        provider = GeminiClient()
        resp = provider.analyze_diff(contents=diff_data)

        if resp.get('status') in ['ERROR', 'SKIPPED']:
            logger.warning(f'Analysis skipped or errored: {resp}')
            return {
                'statusCode': 200,
                'body': json.dumps(resp)
            }

        # Generate markdown report
        markdown_report = format_report_to_markdown(report_data=resp)

        # Call Github API to post report as PR comment
        logger.info(f"Posting comment for {repo_full_name} PR#{pull_request_number}...")
        github_client = GithubClient()
        post_status = github_client.post_comment(repo_full_name=repo_full_name, pr_number=pull_request_number, pr_comments=markdown_report)
        if not post_status:
            return {
                'statusCode': 502,
                'body': json.dumps({'error': "Failed to post comments to Github."})
            }

        # Store report results
        uploader = S3Uploader()
        upload_success = uploader.save_report(resp)

        if not upload_success:
            logger.error("Failed to upload report to S3.")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'S3 Upload Failed.'})
            }
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analysis complete.',
                's3_upload': 'Success',
                'data': resp
            })
        }

    except Exception as e:
        logger.error(f"Critical execution error:{str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

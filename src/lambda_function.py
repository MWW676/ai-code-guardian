import json
import logging
from src.providers.gemini_client import GeminiClient
from src.providers.s3_client import S3Uploader
from src.providers.github_client import GithubClient
from src.utils.markdown_utils import format_report_to_markdown
from src.utils.security_utils import verify_github_signature
import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ssm_client = boto3.client('ssm')

def lambda_handler(event, context):
    # print event for debug ease
    logger.info(f"Received event: {json.dumps(event)}")

    # Retrieve header and event
    headers = event.get('headers', {})
    event_body = event.get('body', '')

    # Filter ping event
    github_event = headers.get('X-GitHub-Event') or headers.get('x-github-event')
    if github_event == 'ping':
        logger.info("Received Github ping event, return 200.")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Pong!'})}

    # Verify Github signature
    try:
        resp = ssm_client.get_parameters(
            Names=['/CodeGuardian/GEMINI_API_KEY', '/CodeGuardian/GITHUB_WEB_SECRET'],
            WithDecryption=True
        )
        if resp.get('InvalidParameters'):
            logger.warning(f"Missing parameters: {resp['InvalidParameters']}")
        params = {p['Name']: p['Value'] for p in resp['Parameters']}
        github_secret_token = params.get('/CodeGuardian/GITHUB_WEB_SECRET')

    except Exception as e:
        logger.error(f"Error fetching parameters: {e}")
        return {'statusCode': 500, 'body': 'Internal Config Error.'}

    github_signature = headers.get('X-Hub-Signature-256') or headers.get('x-hub-signature-256')
    verify_success = verify_github_signature(
        payload_body=event_body,
        signature_header=github_signature,
        secret_token=github_secret_token
    )
    if not verify_success:
        logger.warning(f"[{__name__}] Invalid Github signature.")
        return {'statusCode': 401, 'body': 'Invalid Signature.'}

    # Filter PR action from event
    payload = json.loads(event_body) if isinstance(event_body, str) else event_body
    action = payload.get('action')

    if action not in ['opened', 'synchronize']:
        logger.info(f"Ignoring action {action}. Only open and synchronize actions are supported.")
        return {'statusCode': 200, 'body': json.dumps({'message': f'Action {action} ignored.'})}

    repo_full_name = payload.get('repository', {}).get('full_name')
    pull_request_number = payload.get('pull_request', {}).get('number')
    if not repo_full_name or not pull_request_number:
        logger.error("Missing repo name or PR number metadata.")
        return {'statusCode': 400, 'body': json.dumps({'error': 'Bad payload.'})}

    # Fetch diff and perform analysis
    try:
        # Call Github API to fetch diff
        logger.info(f"Fetching Git diff for {repo_full_name} PR#{pull_request_number}...")
        github_client = GithubClient()
        diff_data = github_client.get_diff(repo_full_name=repo_full_name, pr_number=pull_request_number)
        if diff_data == 'ERROR':
            return {'statusCode': 502, 'body': json.dumps({'error': "Failed to fetch diff from Github."})}

        # Call Gemini API to perform analysis
        logger.info("Starting AI analysis ...")
        provider = GeminiClient()
        resp = provider.analyze_diff(contents=diff_data)

        if resp.get('status') in ['ERROR', 'SKIPPED']:
            logger.warning(f'Analysis skipped or errored: {resp}')
            return {'statusCode': 200, 'body': json.dumps(resp)}

        # Generate report
        markdown_report = format_report_to_markdown(report_data=resp)

        # Call Github API to post report as PR comment
        logger.info(f"Posting comment for {repo_full_name} PR#{pull_request_number}...")
        github_client = GithubClient()
        post_success = github_client.post_comment(repo_full_name=repo_full_name, pr_number=pull_request_number, pr_comments=markdown_report)
        if not post_success:
            logger.error("⚠️ Failed to post comment to GitHub, but proceeding to S3 upload.")

        # Store report results
        uploader = S3Uploader()
        upload_success = uploader.save_report(resp)

        resp_body = {
            'message': 'Analysis complete.',
            's3_upload': 'Success' if upload_success else 'Failed',
            'github_comment': 'Success' if post_success else 'Failed',
            'data': resp
        }
        return {'statusCode': 200, 'body': json.dumps(resp_body)}

    except Exception as e:
        logger.error(f"Critical execution error:{str(e)}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

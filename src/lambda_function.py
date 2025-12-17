import json
import logging
from src.providers.gemini_client import GeminiClient
from src.providers.s3_client import S3Uploader
from src.providers.github_client import GithubClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # print event for debug ease
    logger.info(f"Received event: {event}")
    event_body = event.get('body')
    if not event_body:
        logger.error("No event body provided in event.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing event body.'})
        }
    payload = json.loads(event_body)
    repo_full_name = payload.get('repository', {}).get('full_name')
    if not repo_full_name:
        logger.error("No repo_full_name provided in the event.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing repo_full_name.'})
        }

    pull_request_number = payload.get('pull_request', {}).get('number')
    if not pull_request_number:
        logger.error("No pull_request_number provided in the event.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing pull_request_number.'})
        }

    # Call Github API to retrieve git diff
    github_client = GithubClient()
    try:
        diff_data = github_client.get_diff(repo_full_name=repo_full_name, pr_number=int(pull_request_number))
        if diff_data == 'ERROR':
            logger.warning("Encounter github API error when retrieving git diff for analysis.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': "Github API error."})
            }

    except Exception as e:
        logger.error(f"Critical execution error:{str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    # Call Gemini API to perform analysis on git diff
    try:
        provider = GeminiClient()
        logger.info("Starting AI analysis ...")
        resp = provider.analyze_diff(contents=diff_data)

        if resp.get('status') in ['ERROR', 'SKIPPED']:
            logger.warning(f'Analysis skipped or errored: {resp}')
            return {
                'statusCode': 200,
                'body': json.dumps(resp)
            }

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

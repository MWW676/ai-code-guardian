import json
import logging
from src.utils.security_utils import verify_github_signature
from src.utils.ssm_config_paths import *
import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ssm_client = boto3.client('ssm')
sqs_client = boto3.client('sqs')

def get_configs():
    try:
        names = [
            GITHUB_WEB_SECRET,
            GITLAB_WEB_SECRET,
            SQS_URL
        ]
        resp = ssm_client.get_parameters(Names=names, WithDecryption=True)
        return {p['Name']: p['Value'] for p in resp['Parameters']}
    except Exception as e:
        logger.error(f"Failed to load ssm configs: {e}")
        return {}

def lambda_handler(event, context):
    # print event for debug ease
    logger.info(f"Received event: {json.dumps(event)}")

    # Retrieve header and event
    headers = event.get('headers', {})
    event_body = event.get('body', '')

    # Check platform
    platform = None
    if headers.get('X-GitHub-Event'):
        platform = 'github'
    if headers.get('X-Gitlab-Event'):
        platform = 'gitlab'
    if not platform:
        logger.error("Event received from unknown platform.")
        return {'statusCode': 401, 'body': 'Unrecognized Event.'}

    configs = get_configs()
    if platform == 'github':
        # Filter ping event
        github_event = headers.get('X-GitHub-Event') or headers.get('x-github-event')
        if github_event == 'ping':
            logger.info("Received ping event, return 200.")
            return {'statusCode': 200, 'body': json.dumps({'message': 'Pong!'})}

        # Verify Github signature
        github_secret_token = configs.get(GITHUB_WEB_SECRET)
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

        # Pack msg for SQS
        msg = {'repo_full_name': repo_full_name, 'pr_number': pull_request_number, 'platform': platform}

    elif platform == 'gitlab':
        # Filter event type
        event_type = headers.get('X-Gitlab-Event') or headers.get('x-gitlab-event')

        if event_type != 'Merge Request Hook':
            logger.info(f"Ignoring GitLab event: {event_type}")
            return {'statusCode': 200, 'body': 'Ignore'}

        # 2. Verify gitlab token
        header_token = headers.get('X-Gitlab-Token')
        if header_token != configs.get(GITLAB_WEB_SECRET):
            logger.warning("Invalid GitLab Secret Token")
            return {'statusCode': 401, 'body': 'Unauthorized'}

        # 3. Check payload and filter PR actions
        payload = json.loads(event_body) if isinstance(event_body, str) else event_body
        obj_attr = payload.get('object_attributes', {})
        action = obj_attr.get('action')

        if action not in ['open', 'update']:
            logger.info(f"GitLab action {action} ignored.")
            return {'statusCode': 200, 'body': 'Ignored action'}

        # Extract metadata
        repo_full_name = payload.get('project', {}).get('path_with_namespace')
        pull_request_number = obj_attr.get('iid')
        if not repo_full_name or not pull_request_number:
            logger.error("Missing GitLab metadata")
            return {'statusCode': 400, 'body': 'Bad Request'}

        # Pack msg for SQS
        msg = {'repo_full_name': repo_full_name, 'pr_number': pull_request_number, 'platform': platform}

    try:
        resp = sqs_client.send_message(
            QueueUrl=configs.get(SQS_URL),
            MessageBody=json.dumps(msg)
        )
        logger.info(f"Message sent! ID: {resp['MessageId']}")
        return {'statusCode': 200, 'body': 'Request queued.'}

    except Exception as e:
        logger.error(f"Critical execution error:{str(e)}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

import json
import logging
from src.providers.gemini_client import GeminiClient
from src.providers.s3_client import S3Uploader

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event, context=None):
    # print event for debug ease
    logger.info(f"Received event: {event}")
    event_body = event.get('body')
    if not event_body:
        logger.error("No event body provided in event.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing event body.'})
        }

    diff_data = json.loads(event_body).get('diff_text')
    if not diff_data:
        logger.error("No diff_text provided in the event.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing diff_text.'})
        }

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

import json
import logging
from providers.gemini_client import GeminiClient
from providers.s3_client import S3Uploader

main_logger = logging.getLogger(__name__)
main_logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # print event for debug ease
    main_logger.info(f"Received event: {event}")

    diff_data = event.get('diff_text')
    if not diff_data:
        main_logger.error("No diff_text provided in the event.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing diff_text.'})
        }

    try:
        provider = GeminiClient()
        main_logger.info("Starting AI analysis ...")
        resp = provider.analyze_diff(contents=diff_data)

        if resp.get('status') in ['ERROR', 'SKIPPED']:
            main_logger.warning(f'Analysis skipped or errored: {resp}')
            return {
                'statusCode': 200,
                'body': json.dumps(resp)
            }

        uploader = S3Uploader()
        upload_success = uploader.save_report(resp)

        if not upload_success:
            main_logger.error("Failed to upload report to S3.")
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
        main_logger.error(f"Critical execution error:{str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

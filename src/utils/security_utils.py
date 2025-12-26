
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

def verify_github_signature(payload_body: str, signature_header: str, secret_token: str) -> bool:
    """Verify Github webhook signature."""
    if not signature_header:
        logger.error("Missing X-Hub-Signature-256 header.")
        return False

    hash_object = hmac.new(
        key=secret_token.encode('utf-8'),
        msg=payload_body.encode('utf-8'),
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    result = hmac.compare_digest(expected_signature, signature_header)
    if not result:
        logger.warning(f"Signature mismatch! Module: {__name__}")
    return result
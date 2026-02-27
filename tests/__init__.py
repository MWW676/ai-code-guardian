import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logger.info("Initializing Test Suite package ...")

TEST_ROOT = Path(__file__).parent
TEST_DATA_DIR = TEST_ROOT / "test_data"

import yaml
import os
from pathlib import Path

class ConfigAsset:
    def __init__(self, file_path=Path(__file__).parent.parent / "core" / "policies.yaml"):
        self.file_path = file_path

    @property
    def available_policies(self) -> list:
        """Dynamically retrieves top-level keys from the YAML asset"""
        if not os.path.exists(self.file_path):
            return []

        with open(self.file_path, "r") as f:
            data = yaml.safe_load(f) or {}
            return list(data.keys())

config = ConfigAsset()
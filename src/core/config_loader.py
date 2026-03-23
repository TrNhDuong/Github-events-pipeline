import os
import yaml
from copy import deepcopy


class ConfigLoader:
    def __init__(self, base_path="configs"):
        self.base_path = base_path

    def load(self, relative_path: str) -> dict:
        config = self._load_yaml(relative_path)

        config = self._inject_env(config)
        config = self._merge_common(config)

        self._validate(config)

        return config

    def _load_yaml(self, relative_path: str) -> dict:
        full_path = os.path.join(self.base_path, relative_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Config not found: {full_path}")

        with open(full_path, "r") as f:
            return yaml.safe_load(f)

    def _inject_env(self, config):
        if isinstance(config, dict):
            return {
                k: self._inject_env(v)
                for k, v in config.items()
            }

        elif isinstance(config, list):
            return [self._inject_env(i) for i in config]

        elif isinstance(config, str):
            if config.startswith("${") and config.endswith("}"):
                env_key = config[2:-1]
                return os.getenv(env_key, config)

        return config

    def _merge_common(self, config):
        common_path = os.path.join(self.base_path, "common/default.yml")

        if not os.path.exists(common_path):
            return config

        with open(common_path, "r") as f:
            common_config = yaml.safe_load(f)

        return self._deep_merge(common_config, config)

    def _deep_merge(self, base, override):
        result = deepcopy(base)

        for k, v in override.items():
            if (
                k in result
                and isinstance(result[k], dict)
                and isinstance(v, dict)
            ):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v

        return result

    def _validate(self, config):
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")

        if "source" not in config:
            print("[WARNING] Missing 'source' section")

        if "destination" not in config:
            print("[WARNING] Missing 'destination' section")
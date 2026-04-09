import os
from typing import Dict

import yaml

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory


def resolve_models_config(config_path: str = '') -> str:
    if config_path:
        return os.path.abspath(os.path.expanduser(config_path))

    try:
        package_share = get_package_share_directory('r2_pkg')
        return os.path.join(package_share, 'config', 'models.yaml')
    except PackageNotFoundError:
        return os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'models.yaml')
        )


def load_model_paths(config_path: str = '') -> Dict[str, str]:
    resolved_config = resolve_models_config(config_path)
    config_dir = os.path.dirname(resolved_config)

    with open(resolved_config, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    models = data.get('models', {}) if isinstance(data, dict) else {}
    resolved_paths: Dict[str, str] = {}
    for name, path in models.items():
        model_path = os.path.expanduser(str(path))
        if not os.path.isabs(model_path):
            model_path = os.path.abspath(os.path.join(config_dir, model_path))
        resolved_paths[str(name)] = model_path
    return resolved_paths


def load_models(config_path: str = '') -> Dict[str, object]:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            'r2_pkg requires the ultralytics package to load YOLO models.'
        ) from exc

    models = {}
    for name, path in load_model_paths(config_path).items():
        if not os.path.isfile(path):
            raise FileNotFoundError(f'YOLO model file not found for {name}: {path}')
        models[name] = YOLO(path)
    return models

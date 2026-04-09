from __future__ import annotations

import rclpy
from rclpy.node import Node

from r2_pkg.srv import SetModel

from .model_manager import load_models


class ModelServiceNode(Node):
    INACTIVE_MODEL_ALIASES = frozenset({'none', 'off', 'deactivate', 'inactive'})

    def __init__(self) -> None:
        super().__init__('model_manager')

        self.declare_parameter('models_config', '')
        self.declare_parameter('initial_model', '')

        self.models = load_models(self.get_parameter('models_config').value)
        if not self.models:
            raise RuntimeError('No models were loaded from the configured models.yaml file.')

        requested_model = str(self.get_parameter('initial_model').value).strip()
        if not requested_model or requested_model.lower() in self.INACTIVE_MODEL_ALIASES:
            self._deactivate_models()
        elif requested_model not in self.models:
            raise RuntimeError(
                f'Initial model {requested_model!r} is not available. '
                f'Configured models: {sorted(self.models.keys())}. '
                f'Inactive aliases: {sorted(self.INACTIVE_MODEL_ALIASES)}'
            )
        else:
            self._activate_model(requested_model)

        self.create_service(SetModel, 'set_model', self.handle_set_model)

        active_state = self.active_model_name if self.active_model_name is not None else 'none'
        self.get_logger().info(
            f'Loaded models: {sorted(self.models.keys())}. '
            f'Active model: {active_state}. '
            'No model is activated automatically.'
        )

    def handle_set_model(self, request: SetModel.Request, response: SetModel.Response):
        model_name = request.model_name.strip()
        normalized_model_name = model_name.lower()

        if normalized_model_name in self.INACTIVE_MODEL_ALIASES:
            self._deactivate_models()
            response.success = True
            response.message = (
                'No active model selected. '
                f'Preloaded models retained: {sorted(self.models.keys())}'
            )
            self.get_logger().info(response.message)
            return response

        if model_name not in self.models:
            response.success = False
            response.message = (
                f'Unknown model {model_name!r}. '
                f'Available models: {sorted(self.models.keys())}. '
                f'Inactive aliases: {sorted(self.INACTIVE_MODEL_ALIASES)}'
            )
            return response

        self._activate_model(model_name)

        response.success = True
        response.message = (
            f'Active model switched to {model_name}. '
            'All other preloaded models are inactive.'
        )
        self.get_logger().info(response.message)
        return response

    def _deactivate_models(self) -> None:
        self.active_model_name = None
        self.active_model = None

    def _activate_model(self, model_name: str) -> None:
        # Only one model can be active at a time, so selecting one
        # automatically leaves every other preloaded model inactive.
        self.active_model_name = model_name
        self.active_model = self.models[model_name]


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ModelServiceNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

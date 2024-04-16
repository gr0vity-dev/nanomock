import platform
from nanomock.internal.utils import get_mock_logger


class FeatureToggle:

    def __init__(self):
        self.os_name = platform.system()
        self.logger = get_mock_logger()
        # this way, if we remove the entry, the feature is enabled, even if we forget to remove the toggle code
        self.disabled_features = {
            "config_blkio": self.os_name == 'Darwin',
        }

    def is_feature_disabled(self, feature_name, custom_warning=None):
        disabled = self.disabled_features.get(feature_name, False)

        if not disabled:
            return False

        custom_warning = custom_warning or f"Feature {feature_name} is disabled for {self.os_name}"
        self.logger.warning(custom_warning)
        return True


toggle = FeatureToggle()

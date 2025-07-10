import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
import config


def initialize_sentry():
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        send_default_pii=True,
        traces_sample_rate=1.0,
        profile_session_sample_rate=1.0,
        profile_lifecycle="trace",
        integrations=[
            AwsLambdaIntegration(),
        ],
    )

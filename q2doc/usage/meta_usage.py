from enum import Enum

from q2cli.core.usage import CLIUsage
from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk import usage as usage


class MetaUsage(Enum):
    execution = usage.ExecutionUsage()
    cli = CLIUsage()
    artifact_api = ArtifactAPIUsage()

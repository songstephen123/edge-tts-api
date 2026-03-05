"""
TTS 性能指标收集
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ProviderMetrics:
    """单个引擎的指标"""
    requests: int = 0
    successes: int = 0
    failures: int = 0
    total_duration: float = 0

    @property
    def success_rate(self) -> float:
        if self.requests == 0:
            return 0
        return self.successes / self.requests

    @property
    def avg_duration(self) -> float:
        if self.successes == 0:
            return 0
        return self.total_duration / self.successes


class TTSMetrics:
    """TTS 指标收集器"""

    def __init__(self):
        self._metrics = defaultdict(ProviderMetrics)

    def record_request(self, provider: str):
        self._metrics[provider].requests += 1

    def record_success(self, provider: str, duration: float):
        self._metrics[provider].successes += 1
        self._metrics[provider].total_duration += duration

    def record_failure(self, provider: str):
        self._metrics[provider].failures += 1

    def get_metrics(self) -> dict:
        return {
            provider: {
                "requests": m.requests,
                "successes": m.successes,
                "failures": m.failures,
                "success_rate": m.success_rate,
                "avg_duration": m.avg_duration,
            }
            for provider, m in self._metrics.items()
        }

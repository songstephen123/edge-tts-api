"""
TTS 管理器 - 核心调度器
"""
import asyncio
import logging
import time
from collections import defaultdict
from typing import Optional, List, TYPE_CHECKING

from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError

if TYPE_CHECKING:
    from app.config.tts_config import TTSConfig

logger = logging.getLogger(__name__)


class TTSAllFailedError(TTSProviderError):
    """所有引擎均失败"""
    pass


class TTSManager:
    """TTS 引擎管理器"""

    def __init__(self, config: Optional["TTSConfig"] = None):
        """初始化 TTS 管理器

        Args:
            config: TTS 配置对象，如果为 None 则使用默认值
        """
        self._providers: List[TTSProvider] = []
        self._failure_counts: defaultdict[str, int] = defaultdict(int)
        self._disabled_until: dict[str, float] = {}
        # 使用配置或默认值
        if config:
            self._failure_threshold = config.failure_threshold
            self._cooldown_seconds = config.cooldown_seconds
        else:
            self._failure_threshold = 5
            self._cooldown_seconds = 300

    def register_provider(self, provider: TTSProvider) -> None:
        """注册 TTS 提供者

        Args:
            provider: 要注册的 TTS 提供者实例
        """
        if provider not in self._providers:
            self._providers.append(provider)
            # 按优先级排序（降序，高优先级在前）
            self._providers.sort(key=lambda p: p.priority, reverse=True)
            logger.info(f"注册 TTS 提供者: {provider.name} (优先级: {provider.priority})")

    def get_providers(self) -> List[TTSProvider]:
        """返回已注册提供者副本

        Returns:
            已注册的 TTS 提供者列表副本
        """
        return self._providers.copy()

    def _is_provider_available(self, provider: TTSProvider) -> bool:
        """检查提供者是否可用（考虑冷却）

        Args:
            provider: 要检查的 TTS 提供者

        Returns:
            如果提供者可用返回 True，否则返回 False
        """
        provider_name = provider.name
        if provider_name in self._disabled_until:
            disabled_until = self._disabled_until[provider_name]
            if time.time() < disabled_until:
                logger.debug(f"提供者 {provider_name} 仍在冷却中")
                return False
            # 冷却期已过，重新启用
            del self._disabled_until[provider_name]
            self._failure_counts[provider_name] = 0
            logger.info(f"提供者 {provider_name} 冷却期结束，已重新启用")
        return True

    def _record_failure(self, provider: TTSProvider) -> None:
        """记录失败，可能触发禁用

        Args:
            provider: 失败的 TTS 提供者
        """
        provider_name = provider.name
        self._failure_counts[provider_name] += 1
        count = self._failure_counts[provider_name]

        logger.warning(f"提供者 {provider_name} 失败 ({count}/{self._failure_threshold})")

        if count >= self._failure_threshold:
            # 触发冷却
            cooldown_end = time.time() + self._cooldown_seconds
            self._disabled_until[provider_name] = cooldown_end
            logger.error(
                f"提供者 {provider_name} 达到失败阈值，"
                f"已禁用 {self._cooldown_seconds} 秒"
            )

    def _record_success(self, provider: TTSProvider) -> None:
        """记录成功，重置计数

        Args:
            provider: 成功的 TTS 提供者
        """
        provider_name = provider.name
        if self._failure_counts[provider_name] > 0:
            logger.info(f"提供者 {provider_name} 恢复正常，重置失败计数")
        self._failure_counts[provider_name] = 0

    async def text_to_speech(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
        force_provider: Optional[str] = None
    ) -> TTSResult:
        """按优先级尝试各引擎，失败则降级

        Args:
            text: 要转换的文本
            voice: 音色 ID
            rate: 语速调整
            pitch: 音调调整
            volume: 音量调整
            force_provider: 强制使用指定的提供者名称

        Returns:
            TTSResult 包含音频数据和元数据

        Raises:
            TTSAllFailedError: 所有提供者均失败时抛出
        """
        if not self._providers:
            raise TTSAllFailedError("没有可用的 TTS 提供者")

        # 确定要尝试的提供者列表
        if force_provider:
            providers_to_try = [
                p for p in self._providers
                if p.name == force_provider and self._is_provider_available(p)
            ]
            if not providers_to_try:
                raise TTSAllFailedError(
                    f"指定的提供者 {force_provider} 不可用或未注册"
                )
        else:
            providers_to_try = [
                p for p in self._providers
                if self._is_provider_available(p)
            ]

        if not providers_to_try:
            raise TTSAllFailedError("所有提供者均处于冷却状态")

        last_error = None

        for provider in providers_to_try:
            try:
                logger.debug(f"尝试使用提供者: {provider.name}")
                result = await provider.text_to_speech(
                    text=text,
                    voice=voice,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
                self._record_success(provider)
                logger.info(f"成功使用 {provider.name} 生成语音")
                return result

            except TTSProviderError as e:
                last_error = e
                self._record_failure(provider)
                logger.warning(f"提供者 {provider.name} 失败: {e}")

            except Exception as e:
                last_error = e
                self._record_failure(provider)
                logger.error(f"提供者 {provider.name} 发生意外错误: {e}")

        # 所有提供者都失败了
        raise TTSAllFailedError(
            f"所有 TTS 提供者均失败。最后错误: {last_error}"
        )

    def get_stats(self) -> dict:
        """获取统计信息

        Returns:
            包含提供者统计信息的字典
        """
        return {
            "providers": [
                {
                    "name": p.name,
                    "priority": p.priority,
                    "is_free": p.is_free,
                    "failure_count": self._failure_counts[p.name],
                    "disabled_until": self._disabled_until.get(p.name),
                    "available": self._is_provider_available(p)
                }
                for p in self._providers
            ],
            "total_providers": len(self._providers),
            "available_providers": sum(
                1 for p in self._providers if self._is_provider_available(p)
            )
        }

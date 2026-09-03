from __future__ import annotations

from dataclasses import dataclass
import re

from version import APP_VERSION, BOT_COMPATIBILITY_VERSION


_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_COMPATIBILITY_PATTERN = re.compile(r"^(\d+)\.(\d+)$")


@dataclass(frozen=True)
class VersionInfo:
    major: int
    minor: int
    patch: int

    @property
    def generation(self) -> str:
        return f"{self.major}.{self.minor}"


def parse_version(version: str) -> VersionInfo:
    match = _VERSION_PATTERN.fullmatch(version)

    if match is None:
        raise ValueError(
            f"Invalid application version: {version!r}"
        )

    return VersionInfo(
        major=int(match.group(1)),
        minor=int(match.group(2)),
        patch=int(match.group(3)),
    )


def parse_compatibility_version(version: str) -> tuple[int, int]:
    match = _COMPATIBILITY_PATTERN.fullmatch(version)

    if match is None:
        raise ValueError(
            f"Invalid Bot compatibility version: {version!r}"
        )

    return (
        int(match.group(1)),
        int(match.group(2)),
    )


def is_bot_compatible(
    bot_version: str,
    required_version: str = BOT_COMPATIBILITY_VERSION,
) -> bool:
    bot = parse_version(bot_version)
    required_major, required_minor = (
        parse_compatibility_version(required_version)
    )

    return (
        bot.major == required_major
        and bot.minor == required_minor
    )


def get_version_info() -> dict[str, str | bool]:
    return {
        "app_version": APP_VERSION,
        "bot_compatibility": BOT_COMPATIBILITY_VERSION,
    }


def check_bot_compatibility(
    bot_version: str,
) -> dict[str, str | bool]:
    compatible = is_bot_compatible(bot_version)

    return {
        "app_version": APP_VERSION,
        "required_bot_version": (
            f"{BOT_COMPATIBILITY_VERSION}.x"
        ),
        "bot_version": bot_version,
        "compatible": compatible,
    }

"""Fixture file covering many nested Python structures for ContextWrap."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable


GLOBAL_LIMIT = 3
GLOBAL_LABEL = "context-wrap"
GLOBAL_REGISTRY: dict[str, int] = {"boot": 1}


def trace(tag: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        def wrapper(*args: object, **kwargs: object) -> object:
            print(f"[{tag}] {func.__name__}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


@dataclass
class Config:
    root: Path
    retries: int = 2
    flags: dict[str, bool] = field(default_factory=lambda: {"debug": False})

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    @classmethod
    def from_name(cls, name: str) -> "Config":
        base = Path("/tmp") / name
        return cls(root=base, flags={"debug": True})


class Processor:
    shared_scale = 10

    def __init__(self, config: Config) -> None:
        self.config = config
        self.items: list[int] = []
        self.status = "idle"

    @trace("process")
    def process(self, values: Iterable[int]) -> dict[str, object]:
        total = 0
        errors: list[str] = []

        for index, value in enumerate(values):
            if value < 0:
                errors.append(f"negative:{value}")
                continue

            adjusted = value * self.shared_scale
            self.items.append(adjusted)
            total += adjusted

        summary = {
            "total": total,
            "count": len(self.items),
            "debug": self.config.flags.get("debug", False),
            "errors": errors,
        }

        return summary

    def with_nested_logic(self, seed: int) -> int:
        counter = seed

        def accumulate(step: int) -> int:
            nonlocal counter
            counter += step

            def finalize(multiplier: int) -> int:
                return counter * multiplier

            return finalize(2)

        return accumulate(3)

    @staticmethod
    def normalize(name: str) -> str:
        return name.strip().lower().replace(" ", "-")


def complex_workflow(config_name: str, payload: list[dict[str, object]]) -> list[str]:
    config = Config.from_name(config_name)
    processor = Processor(config)
    lines: list[str] = []

    with suppress(FileNotFoundError):
        marker_path = config.cache_dir / "marker.txt"
        marker_path.unlink()

    for entry in payload:
        match entry:
            case {"kind": "point", "value": int(value)} if value > 0:
                lines.append(f"point:{value}")
            case {"kind": "label", "value": str(text)}:
                lines.append(Processor.normalize(text))
            case {"kind": "batch", "value": list(values)}:
                result = processor.process(values)
                lines.append(f"batch:{result['count']}")
            case _:
                lines.append("unknown")

    try:
        computed = [
            f"{idx}:{item}"
            for idx, item in enumerate(lines)
            if idx < GLOBAL_LIMIT and item != "unknown"
        ]
        mapping = {item: len(item) for item in computed}
        chosen = next((name for name in mapping if "batch" in name), "missing")
        lines.append(chosen)
    except StopIteration:
        lines.append("empty")
    finally:
        GLOBAL_REGISTRY[config_name] = len(lines)

    return lines


def outer_scope(flag: bool) -> Callable[[int], int]:
    outer_value = 5

    def inner_scope(delta: int) -> int:
        local_value = outer_value + delta
        return local_value if flag else delta

    return inner_scope


async def consume(stream: Iterable[int]) -> list[int]:
    results: list[int] = []

    for value in stream:
        if value % 2 == 0:
            results.append(value)
        else:
            await maybe_log(value)

    return results


async def maybe_log(value: int) -> None:
    if value > 10:
        print(f"large={value}")


def walrus_and_comprehensions(raw_values: list[str]) -> tuple[list[int], dict[str, int]]:
    cleaned = [int(stripped) for text in raw_values if (stripped := text.strip())]
    grouped = {f"value-{number}": number for number in cleaned if number % 2 == 0}
    return cleaned, grouped


if __name__ == "__main__":
    sample_payload = [
        {"kind": "point", "value": 4},
        {"kind": "label", "value": "Needs Cleanup"},
        {"kind": "batch", "value": [1, 2, -3]},
    ]
    print(complex_workflow("demo", sample_payload))

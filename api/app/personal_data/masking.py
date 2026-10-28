from dataclasses import dataclass, field

from app.personal_data.detectors import detect_all
from app.personal_data.hashing import IdentifierHasher


@dataclass(frozen=True)
class MaskedText:
    """Text safe to send to a model, and how to map the model's quotes back to the original."""

    text: str
    originals: dict[str, str] = field(default_factory=dict)  # placeholder -> original value

    def restore(self, quote: str) -> str:
        for placeholder, original in self.originals.items():
            quote = quote.replace(placeholder, original)
        return quote


def mask_for_model(text: str, hasher: IdentifierHasher) -> MaskedText:
    parts: list[str] = []
    originals: dict[str, str] = {}
    position = 0
    for detection in detect_all(text):
        placeholder = hasher.placeholder(detection.kind, detection.value)
        originals[placeholder] = detection.value
        parts += [text[position : detection.start], placeholder]
        position = detection.end
    parts.append(text[position:])
    return MaskedText("".join(parts), originals)

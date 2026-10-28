"""Tesseract as a subprocess: free, offline, installed in the API image with its Romanian pack."""

import asyncio
import shutil

from app.ocr.base import EngineStatus, OcrError, RecognizedPage, RecognizedWord

INSTALL_HINT = "Install tesseract-ocr and tesseract-ocr-ron (api/Dockerfile does), then restart."


def parse_tsv(tsv: str) -> RecognizedPage:
    """Words and lines from `tesseract ... tsv` output.

    Columns: level, page, block, paragraph, line, word, left, top, width, height, conf, text.
    Level 5 rows are words; a conf of -1 marks layout rows without text.
    """
    words: list[RecognizedWord] = []
    lines: dict[tuple[str, str, str], list[str]] = {}
    for row in tsv.splitlines()[1:]:
        fields = row.split("\t")
        if len(fields) < 12 or fields[0] != "5":
            continue
        text, confidence = fields[11].strip(), float(fields[10])
        if not text or confidence < 0:
            continue
        left, top, width, height = (float(value) for value in fields[6:10])
        words.append(RecognizedWord(text, left, top, left + width, top + height, confidence / 100))
        lines.setdefault((fields[2], fields[3], fields[4]), []).append(text)
    text = "\n".join(" ".join(line) for line in lines.values())
    return RecognizedPage(text, words)


class TesseractEngine:
    name = "tesseract"

    def __init__(self, languages: str, timeout_seconds: float) -> None:
        self._languages = languages
        self._timeout = timeout_seconds

    async def recognize(self, png: bytes, dpi: int) -> RecognizedPage:
        output = await self._run(
            ["stdin", "stdout", "-l", self._languages, "--dpi", str(dpi), "tsv"], png
        )
        return parse_tsv(output)

    async def probe(self) -> EngineStatus:
        try:
            version = (await self._run(["--version"])).splitlines()[0].strip()
            installed = (await self._run(["--list-langs"])).splitlines()[1:]
        except OcrError as error:
            return EngineStatus(self.name, False, None, [], str(error))
        missing = [lang for lang in self._languages.split("+") if lang not in installed]
        detail = (
            f"Missing language packs: {', '.join(missing)}. {INSTALL_HINT}" if missing else None
        )
        return EngineStatus(self.name, not missing, version, sorted(installed), detail)

    async def _run(self, arguments: list[str], stdin: bytes | None = None) -> str:
        binary = shutil.which("tesseract")
        if binary is None:
            raise OcrError(f"Tesseract is not installed. {INSTALL_HINT}")
        process = await asyncio.create_subprocess_exec(
            binary,
            *arguments,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            output, errors = await asyncio.wait_for(process.communicate(stdin), self._timeout)
        except TimeoutError as error:
            process.kill()
            await process.wait()
            raise OcrError(f"Tesseract took longer than {self._timeout:.0f} s.") from error
        if process.returncode != 0:
            message = errors.decode(errors="replace").strip()[-300:]
            raise OcrError(f"Tesseract failed: {message}")
        return output.decode(errors="replace")

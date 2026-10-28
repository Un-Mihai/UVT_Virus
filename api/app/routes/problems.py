from typing import Any

from pydantic import BaseModel


class Problem(BaseModel):
    detail: str


# What the product routes answer with {"detail": "<sentence>"}, declared so the web's generated
# types know `detail` is text. Explicit codes: a "4XX" range would drop FastAPI's own 422.
PROBLEMS: dict[int | str, dict[str, Any]] = {
    code: {"model": Problem} for code in (400, 403, 404, 409, 413, 415, 503)
}

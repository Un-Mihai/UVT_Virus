from pydantic import SecretStr

from app.personal_data import IdentifierHasher, detect_all, mask_for_model
from tests.test_romanian import make_cnp

CNP = make_cnp("190010112345")  # synthetic
OTHER_CNP = make_cnp("280020212345")
HASHER = IdentifierHasher(SecretStr("test-key"))


def test_finds_valid_cnps_and_labelled_invalid_ones_only() -> None:
    broken = CNP[:-1] + str((int(CNP[-1]) + 1) % 10)
    text = f"CNP {CNP}. Cod CNP: {broken}. Nr. contract 1234567890123."

    found = detect_all(text)

    assert [(d.value, d.valid) for d in found] == [(CNP, True), (broken, False)]
    assert text[found[0].start : found[0].end] == CNP


def test_same_cnp_gets_the_same_hash_and_placeholder_and_restores() -> None:
    masked = mask_for_model(f"Ion Pop, CNP {CNP}; Ana Pop, CNP {OTHER_CNP}; again {CNP}", HASHER)

    assert CNP not in masked.text
    assert OTHER_CNP not in masked.text
    placeholder = HASHER.placeholder("cnp", CNP)
    assert masked.text.count(placeholder) == 2
    assert masked.restore(f"CNP {placeholder}") == f"CNP {CNP}"


def test_hashes_depend_on_the_key() -> None:
    other = IdentifierHasher(SecretStr("another-key"))

    assert HASHER.hash("cnp", CNP) == HASHER.hash("cnp", CNP)
    assert HASHER.hash("cnp", CNP) != other.hash("cnp", CNP)
    assert HASHER.hash("cnp", CNP) != HASHER.hash("cnp", OTHER_CNP)


def test_mask_keeps_only_the_ends() -> None:
    assert IdentifierHasher.mask("1900101123456") == "1*********456"

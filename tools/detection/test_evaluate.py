"""Prueba de cordura del evaluador (pytest o ejecución directa)."""

from evaluate import evaluate, sanity_check


def test_reference_boxes() -> None:
    sanity_check()


def test_empty_preds() -> None:
    r = evaluate({"a": [(0.1, 0.1, 0.3, 0.3)]}, {}, ["a"], 0.5)
    assert r["recall"] == 0 and r["fp"] == 0


def test_false_box() -> None:
    r = evaluate(
        {"a": [(0.1, 0.1, 0.3, 0.3)]}, {"a": [((0.6, 0.6, 0.9, 0.9), 0.9)]}, ["a"], 0.5
    )
    assert r["recall"] == 0 and r["fp"] == 1


if __name__ == "__main__":
    test_reference_boxes()
    test_empty_preds()
    test_false_box()
    print("ok")

from backend.app.hf_pipeline import analyze_driver_state


def test_analyze_driver_state_returns_structured_result():
    result = analyze_driver_state("I lost grip in turn 4", lap=24)

    assert result["alert_level"] in {"NORMAL", "ELEVATED", "CRITICAL"}
    assert result["stress_index"] >= 0
    assert result["stress_index"] <= 1
    assert "strategy" in result
    assert result["strategy"]["recommended_pit_lap"] >= 1

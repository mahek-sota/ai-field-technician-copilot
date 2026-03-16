"""
Tests for HTTP route layer — verifies request/response shapes and status codes.
Uses the real data directory (5 pre-loaded machines) and mock LLM.
"""
import pytest


class TestRootEndpoints:
    def test_root_returns_ok(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_root_contains_app_name(self, client):
        assert "app" in client.get("/").json()

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestMachinesListRoute:
    def test_get_machines_returns_list(self, client):
        resp = client.get("/machines/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_machines_has_required_fields(self, client):
        for item in client.get("/machines/").json():
            for field in ("machine_id", "name", "type", "status", "location"):
                assert field in item, f"Missing field '{field}' in machine list item"

    def test_get_machines_status_values_are_valid(self, client):
        valid = {"normal", "warning", "critical", "offline"}
        for item in client.get("/machines/").json():
            assert item["status"] in valid

    def test_get_machines_includes_all_five_machines(self, client):
        ids = {m["machine_id"] for m in client.get("/machines/").json()}
        for mid in ("conveyor_1", "conveyor_2", "robotic_arm_1", "pump_4", "compressor_2"):
            assert mid in ids, f"Expected machine '{mid}' in list"

    def test_conveyor_1_is_normal(self, client):
        by_id = {m["machine_id"]: m for m in client.get("/machines/").json()}
        assert by_id["conveyor_1"]["status"] == "normal"

    def test_conveyor_2_is_warning(self, client):
        by_id = {m["machine_id"]: m for m in client.get("/machines/").json()}
        assert by_id["conveyor_2"]["status"] == "warning"

    def test_robotic_arm_is_critical(self, client):
        by_id = {m["machine_id"]: m for m in client.get("/machines/").json()}
        assert by_id["robotic_arm_1"]["status"] == "critical"


class TestMachineDetailRoute:
    def test_get_machine_status_valid(self, client):
        assert client.get("/machines/conveyor_1").status_code == 200

    def test_get_machine_status_not_found(self, client):
        assert client.get("/machines/nonexistent_xyz").status_code == 404

    def test_get_machine_status_has_sensors(self, client):
        body = client.get("/machines/conveyor_1").json()
        assert "sensors" in body
        assert len(body["sensors"]) > 0

    def test_get_machine_status_sensor_fields(self, client):
        for sensor in client.get("/machines/conveyor_1").json()["sensors"]:
            for field in ("name", "value", "unit", "status"):
                assert field in sensor

    def test_get_machine_has_machine_id(self, client):
        assert client.get("/machines/conveyor_1").json()["machine_id"] == "conveyor_1"

    def test_get_machine_has_required_fields(self, client):
        body = client.get("/machines/conveyor_1").json()
        for f in ("machine_id", "name", "type", "location", "status", "last_updated", "recent_errors"):
            assert f in body

    def test_conveyor_2_warning_status(self, client):
        assert client.get("/machines/conveyor_2").json()["status"] == "warning"

    def test_robotic_arm_critical_status(self, client):
        assert client.get("/machines/robotic_arm_1").json()["status"] == "critical"

    def test_pump_4_critical_status(self, client):
        assert client.get("/machines/pump_4").json()["status"] == "critical"


class TestDiagnoseRoute:
    def test_diagnose_valid_request(self, client):
        assert client.post("/diagnose", json={"machine_id": "conveyor_1"}).status_code == 200

    def test_diagnose_invalid_machine_returns_404(self, client):
        assert client.post("/diagnose", json={"machine_id": "no_such_machine"}).status_code == 404

    def test_diagnose_response_schema(self, client):
        body = client.post("/diagnose", json={"machine_id": "conveyor_1"}).json()
        assert body["success"] is True
        result = body["result"]
        for f in ("machine_id", "timestamp", "diagnosis", "recommended_action",
                  "severity", "confidence_score", "supporting_evidence", "source"):
            assert f in result

    def test_diagnose_confidence_range(self, client):
        score = client.post("/diagnose", json={"machine_id": "conveyor_1"}).json()["result"]["confidence_score"]
        assert 0.0 <= score <= 1.0

    def test_diagnose_severity_valid(self, client):
        severity = client.post("/diagnose", json={"machine_id": "conveyor_1"}).json()["result"]["severity"]
        assert severity in ("low", "medium", "high", "critical")

    def test_diagnose_source_valid(self, client):
        source = client.post("/diagnose", json={"machine_id": "conveyor_1"}).json()["result"]["source"]
        assert source in ("llm", "rules_fallback", "cache")

    def test_diagnose_machine_id_in_result(self, client):
        assert client.post("/diagnose", json={"machine_id": "conveyor_1"}).json()["result"]["machine_id"] == "conveyor_1"

    def test_diagnose_critical_machine_severity(self, client):
        """robotic_arm_1 has critical sensor — rules engine short-circuits to critical."""
        result = client.post("/diagnose", json={"machine_id": "robotic_arm_1"}).json()["result"]
        assert result["severity"] == "critical"
        assert result["source"] == "rules_fallback"

    def test_diagnose_pump4_rules_fallback(self, client):
        """pump_4 has critical pressure — high-confidence rule fires."""
        result = client.post("/diagnose", json={"machine_id": "pump_4"}).json()["result"]
        assert result["source"] == "rules_fallback"

    def test_diagnose_force_refresh_accepted(self, client):
        body = client.post("/diagnose", json={"machine_id": "conveyor_1", "force_refresh": True}).json()
        assert body["success"] is True

    def test_diagnose_include_logs_false_accepted(self, client):
        body = client.post("/diagnose", json={"machine_id": "conveyor_1", "include_logs": False}).json()
        assert body["success"] is True

    def test_get_history_returns_list(self, client):
        resp = client.get("/machines/conveyor_1/history")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_history_unknown_machine_returns_empty(self, client):
        resp = client.get("/machines/nonexistent_xyz/history")
        assert resp.status_code == 200
        assert resp.json() == []

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_scaffolding_files_exist_and_reference_the_fastapi_app():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "digital_twin_lab.main:app" in dockerfile
    assert "APP_PORT=8017" in env_example


def test_kubernetes_manifests_are_coherent_for_single_app_deployment():
    deployment = yaml.safe_load((ROOT / "k8s" / "deployment.yaml").read_text(encoding="utf-8"))
    service = yaml.safe_load((ROOT / "k8s" / "service.yaml").read_text(encoding="utf-8"))

    deployment_labels = deployment["spec"]["template"]["metadata"]["labels"]
    service_selector = service["spec"]["selector"]
    container = deployment["spec"]["template"]["spec"]["containers"][0]

    assert service_selector == deployment_labels
    assert "digital_twin_lab.main:app" in " ".join(container.get("command", []))


def test_engram_project_config_uses_project_name_key():
    config = json.loads((ROOT / ".engram" / "config.json").read_text(encoding="utf-8"))

    assert config["project_name"] == "17-digital-twin-simulation-lab"

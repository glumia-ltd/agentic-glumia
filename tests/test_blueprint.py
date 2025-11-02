from src.models import Blueprint
import yaml

def test_example_blueprint_loads():
    data = yaml.safe_load(open("examples/website_redesign.yaml"))
    bp = Blueprint.model_validate(data)
    assert bp.project.id == "website-redesign"
    assert len(bp.phases) >= 3

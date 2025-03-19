import json
import os
from pathlib import Path

import yaml

from py_semantic_taxonomy.app import create_app

if __name__ == "__main__":
    os.environ["PyST_db_backend"] = "sqlite"
    output_dir = Path(__file__).parent.parent / "docs" / "api"

    app = create_app()
    openapi = app.openapi()
    openapi["info"]["x-logo"] = {
        "url": "https://docs.pyst.dev/logo.png"
    }

    with open(output_dir / "openapi.json", "w") as f:
        json.dump(openapi, f, indent=2)
    with open(output_dir / "openapi.yaml", "w") as f:
        yaml.dump(openapi, f, sort_keys=False)

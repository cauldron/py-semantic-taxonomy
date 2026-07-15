"""Seed a running PyST instance with Combined Nomenclature data.

Env-driven so it works both from the Compose `seed` service and standalone.
See docs-src/common-workflows.md.
"""

import os

from pyst_client.cn import CombinedNomenclatureLoader


def _flag(name: str, *, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def main() -> None:
    """Load Combined Nomenclature data into the PyST instance named by the env vars."""
    CombinedNomenclatureLoader(
        year=int(os.environ.get("SEED_YEAR", "2024")),
        api_key=os.environ["PYST_AUTH_TOKEN"],
        host=os.environ.get("PYST_HOST", "http://app:8000"),
        sample=_flag("SEED_SAMPLE", default=True),
    ).write()


if __name__ == "__main__":
    main()

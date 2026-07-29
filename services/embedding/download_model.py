import argparse
import shutil
from pathlib import Path

from huggingface_hub import snapshot_download

REPO_ID = "Xenova/all-MiniLM-L6-v2"
REVISION = "751bff37182d3f1213fa05d7196b954e230abad9"
REQUIRED_FILES = ("onnx/model.onnx", "tokenizer.json", "tokenizer_config.json", "config.json")
FLATTENED = {"onnx/model.onnx": "model.onnx"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the embedding model.")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    staging = args.out / ".staging"
    snapshot_download(
        repo_id=REPO_ID,
        revision=REVISION,
        allow_patterns=list(REQUIRED_FILES),
        local_dir=staging,
    )

    args.out.mkdir(parents=True, exist_ok=True)
    for source in REQUIRED_FILES:
        target = args.out / FLATTENED.get(source, Path(source).name)
        shutil.copyfile(staging / source, target)
        print(f"{target.name}: {target.stat().st_size} bytes")

    shutil.rmtree(staging)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

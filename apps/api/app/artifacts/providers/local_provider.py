from pathlib import Path
from app.artifacts.base import ArtifactProvider


class LocalArtifactProvider(ArtifactProvider):
    def generate(self, request_type: str, title: str, content: str, context: dict, output_dir: str) -> dict:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if request_type == "generate_patch_artifact":
            filename = context.get("filename", "proposed-change.patch")
            body = content or "# Patch Artifact\n\n" + title
            artifact_type = "patch"

        elif request_type == "generate_diff_preview":
            filename = context.get("filename", "diff-preview.md")
            body = content or f"# Diff Preview\n\nTitle: {title}\n\n```diff\n+ proposed change\n- previous change\n```"
            artifact_type = "diff_preview"

        elif request_type == "generate_change_bundle":
            filename = context.get("filename", "change-bundle.json")
            body = content or '{"changes":["example change"],"notes":"generated bundle"}'
            artifact_type = "change_bundle"

        elif request_type == "attach_artifact_to_task":
            filename = context.get("filename", "attachment.txt")
            body = content or title
            artifact_type = "attachment"

        else:
            raise ValueError(f"Unsupported artifact request type: {request_type}")

        target = out_dir / filename
        target.write_text(body, encoding="utf-8")

        return {
            "status": "success",
            "artifact_type": artifact_type,
            "title": title,
            "file_path": str(target),
            "metadata_json": {
                "request_type": request_type,
                "filename": filename,
            }
        }

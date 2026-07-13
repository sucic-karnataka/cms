import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SLUG_LEN = 80
MAX_ALIAS_SEGMENT_BYTES = 180


def parse_front_matter(text: str) -> list[str]:
    lines = text.splitlines()
    if len(lines) < 2 or lines[0].strip() != "---":
        return []

    front_matter = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        front_matter.append(line)
    return front_matter


def main() -> int:
    errors: list[str] = []

    for path in CONTENT_DIR.rglob("*.md"):
        front_matter = parse_front_matter(path.read_text(encoding="utf-8"))
        in_aliases = False

        for line in front_matter:
            stripped = line.strip()

            if stripped.startswith("slug:"):
                slug = stripped.split(":", 1)[1].strip().strip("'\"")
                if not slug:
                    errors.append(f"{path}: empty slug")
                elif len(slug) > MAX_SLUG_LEN:
                    errors.append(f"{path}: slug '{slug}' exceeds {MAX_SLUG_LEN} characters")
                elif not SLUG_RE.fullmatch(slug):
                    errors.append(
                        f"{path}: slug '{slug}' must use lowercase ASCII letters, numbers, and hyphens only"
                    )

            if stripped == "aliases:":
                in_aliases = True
                continue

            if in_aliases:
                if line.startswith("  - "):
                    alias = line[4:].strip().strip("'\"")
                    segment = alias.rstrip("/").split("/")[-1]
                    segment_bytes = len(segment.encode("utf-8"))
                    if segment_bytes > MAX_ALIAS_SEGMENT_BYTES:
                        errors.append(
                            f"{path}: alias segment '{segment}' is {segment_bytes} bytes; "
                            f"keep aliases under {MAX_ALIAS_SEGMENT_BYTES} UTF-8 bytes"
                        )
                    continue

                if line and not line.startswith(" "):
                    in_aliases = False

    if errors:
        print("Content path validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Content path validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build exactly the checklist deliverables, with no runtime databases or secrets."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

BASE = Path(__file__).resolve().parent
FILES = (
    "agent.py", "hitl.py", "requirements.txt",
    "evidence/full-trace.png", "evidence/blocked-gate.png",
    "evidence/runs-ABC.txt", "FINDINGS.pdf",
)


def main():
    for name in FILES:
        path = BASE / name
        if not path.is_file() or not path.stat().st_size:
            raise FileNotFoundError(f"Missing required deliverable: {name}")
    target = BASE / "s11-assignment.zip"
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(BASE / name, f"s11-assignment/{name}")
    with ZipFile(target) as archive:
        assert archive.namelist() == [f"s11-assignment/{name}" for name in FILES]
        assert archive.testzip() is None
    print(target)
    print("Verified exactly", len(FILES), "files:")
    print("\n".join(FILES))


if __name__ == "__main__":
    main()

from pathlib import Path


def list_files(path="."):
    p = Path(path)

    if not p.exists():
        return f"ERROR: {path} does not exist"

    return "\n".join(str(x) for x in p.iterdir())


def read_file(path):
    p = Path(path)

    if not p.exists():
        return f"ERROR: {path} does not exist"

    return p.read_text()


def write_file(path, content):
    p = Path(path)

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

    return f"WROTE {path}"

def run_command(cmd):
    import subprocess

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    return result.stdout + result.stderr

def search_code(query, path="."):
    import subprocess

    result = subprocess.run(
        f"grep -rnw '{path}' -e '{query}'",
        shell=True,
        capture_output=True,
        text=True
    )

    return result.stdout + result.stderr

def run_tests():
    import subprocess

    result = subprocess.run(
        "pytest",
        shell=True,
        capture_output=True,
        text=True
    )

    return result.stdout + result.stderr

TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "search_code": search_code,
    "run_command": run_command,
    "run_tests": run_tests,
}
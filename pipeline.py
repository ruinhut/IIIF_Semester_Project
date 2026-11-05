"""Portable repository launcher; use the project environment automatically."""
from pathlib import Path
import os
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
CODE = ROOT / "Code_git"
ENVIRONMENT = CODE / ".venv"
PYTHON = ENVIRONMENT / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main():
    arguments = sys.argv[1:]
    if "--setup" in arguments:
        if not PYTHON.exists():
            venv.EnvBuilder(with_pip=True).create(ENVIRONMENT)
        command = [str(PYTHON), "-m", "pip", "install"]
        for folder in [*(f"Module_{n}" for n in range(1, 9)), "Pipeline_Runner"]:
            command += ["-e", str(CODE / folder)]
        command += ["pytest", "Pillow", "certifi"]
        result = subprocess.run(command)
        if result.returncode:
            return result.returncode
        arguments.remove("--setup")
        if not arguments:
            print("Setup complete. Run: python pipeline.py --help")
            return 0
    if PYTHON.exists() and Path(sys.executable).resolve() != PYTHON.resolve():
        return subprocess.call([str(PYTHON), str(Path(__file__).resolve()), *arguments])
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        import certifi
        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    except ImportError:
        pass
    sys.path.insert(0, str(CODE / "Pipeline_Runner"))
    from iiif_pipeline_runner.launcher import main as launch
    return launch(arguments)


if __name__ == "__main__":
    raise SystemExit(main())

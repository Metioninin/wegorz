import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile

from const import Lang

# TODO: make it more dynamic to allow for reloading
CPP_TIMEOUT = 1
PYTHON_TIMEOUT = 10


@dataclass
class Executor:
    exec_path: Path
    lang: Lang
    box_id: int

    _proc: subprocess.Popen | None = None
    _timeout: float | None = None

    def start(self) -> None:
        # setup
        result = subprocess.run(
            args=["isolate", f"--box-id={self.box_id}", "--init"],
            capture_output=True,
            text=True,
            check=True,
        )
        sandbox_dir = Path(result.stdout.strip()) / "box"
        exec_file = sandbox_dir / "exec"
        copyfile(self.exec_path, exec_file)

        # run
        if self.lang == "CPP":
            self._timeout = CPP_TIMEOUT

            os.chmod(exec_file, 0o755)

            options = []
            command = ["./exec"]
        else:
            self._timeout = PYTHON_TIMEOUT

            python_path = Path("/opt") / "python-standalone"
            python_bin_path = python_path / "bin" / "python"

            options = [f"--dir={python_path}"]
            command = [str(python_bin_path), "exec"]

        options += [f"--box-id={self.box_id}"]

        self._proc = subprocess.Popen(
            args=["isolate"] + options + ["--run", "--"] + command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=sandbox_dir,
            text=True,
        )

    def communicate(self, msg: str) -> tuple[str, str] | None:
        if self._proc is None:
            return None

        try:
            stdout, stderr = self._proc.communicate(input=msg, timeout=self._timeout)
            return stdout, stderr
        except subprocess.TimeoutExpired:
            self.exit()

        return None

    def exit(self) -> None:
        if self._proc is not None:
            self._proc.kill()
            self._proc = None
            subprocess.run(["isolate", "--cleanup"])

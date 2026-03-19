from pathlib import Path
import subprocess
import sys


def main() -> int:
	script_dir = Path(__file__).resolve().parent
	main_py = script_dir / "main.py"

	cmd = [
		sys.executable,
		str(main_py),
		"--ct-folder",
		r"C:\Users\whisk\Downloads\Senior Design\Multi_Modal_Spring2026\120kv_FDK",
		"--downsample",
		"3",
		"--roi-sx", # Overestimates the size. it will size down in rest of code.
		"3000",
		"--roi-sy",
		"3000",
		"--roi-sz",
		"3000",
		"--mc-level", # 42000 GOOD
		"42000",
		"--n-points", # somewhere 2000-5000 is good enough for RANSAC
		"4000",
	]

	return subprocess.call(cmd)


if __name__ == "__main__":
	raise SystemExit(main())
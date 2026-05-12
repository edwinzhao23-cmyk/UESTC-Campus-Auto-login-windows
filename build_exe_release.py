#!/usr/bin/env python
# -*- coding:utf-8 -*-
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
RELEASE_ROOT = ROOT / "release"


def run(args):
    print(" ".join(str(arg) for arg in args))
    subprocess.check_call([str(arg) for arg in args], cwd=str(ROOT))


def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        run([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-i",
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "pyinstaller",
        ])


def build_exes():
    targets = [
        ("UESTC_Setup_Wizard", "setup_gui.py", "--windowed"),
        ("background_runner", "background_runner.py", "--windowed"),
        ("login_once", "login_once.py", "--console"),
        ("log_cleanup", "log_cleanup.py", "--windowed"),
    ]
    for name, script, mode in targets:
        run([
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            mode,
            "--name",
            name,
            script,
        ])


def copy_file(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def create_package():
    RELEASE_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    package_name = f"UESTC-AutoLogin-EXE-{stamp}"
    package_dir = RELEASE_ROOT / package_name
    zip_path = RELEASE_ROOT / f"{package_name}.zip"

    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    (package_dir / "logs").mkdir()

    root_files = [
        ".gitignore",
        "always_online.py",
        "app_paths.py",
        "background_runner.py",
        "build_exe_release.py",
        "config_loader.py",
        "config.example.py",
        "LICENSE",
        "logger.py",
        "login_once.py",
        "log_cleanup.py",
        "notifier.py",
        "README.md",
        "requirements.txt",
        "setup_gui.py",
        "使用说明.md",
        "__init__.py",
    ]
    for name in root_files:
        copy_file(ROOT / name, package_dir / name)

    copy_file(ROOT / "config.example.py", package_dir / "config.py")
    copy_file(ROOT / "dist" / "UESTC_Setup_Wizard.exe", package_dir / "UESTC_Setup_Wizard.exe")
    copy_file(ROOT / "dist" / "background_runner.exe", package_dir / "background_runner.exe")
    copy_file(ROOT / "dist" / "login_once.exe", package_dir / "login_once.exe")
    copy_file(ROOT / "dist" / "log_cleanup.exe", package_dir / "log_cleanup.exe")

    bit_files = ["LoginManager.py", "_decorators.py", "__init__.py"]
    for name in bit_files:
        copy_file(ROOT / "BitSrunLogin" / name, package_dir / "BitSrunLogin" / name)

    enc_files = ["srun_base64.py", "srun_md5.py", "srun_sha1.py", "srun_xencode.py", "__init__.py"]
    for name in enc_files:
        copy_file(ROOT / "BitSrunLogin" / "encryption" / name, package_dir / "BitSrunLogin" / "encryption" / name)

    (package_dir / "logs" / ".placeholder").write_text("", encoding="utf-8")

    if zip_path.exists():
        zip_path.unlink()
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for path in package_dir.rglob("*"):
            archive.write(path, path.relative_to(RELEASE_ROOT))

    print(f"发布目录：{package_dir}")
    print(f"压缩包：{zip_path}")


def main():
    ensure_pyinstaller()
    build_exes()
    create_package()


if __name__ == "__main__":
    main()

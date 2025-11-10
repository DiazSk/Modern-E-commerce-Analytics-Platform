"""
Quick Environment Check Script
Verifies prerequisites before data generation
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9 and version.minor < 12:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(
            f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.9, 3.10, or 3.11"
        )
        return False


def check_dependencies():
    """Check required packages"""
    required = ["pandas", "faker", "psycopg2", "python-dotenv"]
    missing = []

    for package in required:
        try:
            if package == "python-dotenv":
                import dotenv
            else:
                __import__(package.replace("-", "_"))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} NOT installed")
            missing.append(package)

    return len(missing) == 0


def check_docker():
    """Check if Docker services are running"""
    import subprocess

    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)

        if "ecommerce-postgres-source" in result.stdout:
            print("✅ PostgreSQL source database running")
            return True
        else:
            print("❌ PostgreSQL source database NOT running")
            print("   Run: docker-compose up -d")
            return False
    except Exception as e:
        print(f"❌ Docker check failed: {str(e)}")
        return False


def check_env_file():
    """Check .env file exists"""
    if Path(".env").exists():
        print("✅ .env file exists")
        return True
    else:
        print("❌ .env file NOT found")
        print("   Run: cp .env.example .env")
        return False


def check_directories():
    """Check required directories"""
    dirs = ["scripts", "data", "dags", "logs"]
    all_exist = True

    for d in dirs:
        if Path(d).exists():
            print(f"✅ {d}/ directory exists")
        else:
            print(f"❌ {d}/ directory missing")
            all_exist = False

    return all_exist


def main():
    print("=" * 50)
    print("Environment Check - Data Generation")
    print("=" * 50)
    print()

    checks = [
        ("Python Version", check_python_version()),
        ("Dependencies", check_dependencies()),
        ("Docker Services", check_docker()),
        ("Environment File", check_env_file()),
        ("Directory Structure", check_directories()),
    ]

    print()
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)

    all_passed = all(result for _, result in checks)

    for name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    if all_passed:
        print("🎉 All checks passed! Ready to generate data.")
        print()
        print("Next steps:")
        print("  1. python scripts/generate_data.py")
        print("  2. python scripts/load_data.py")
    else:
        print("⚠️ Some checks failed. Fix issues above before proceeding.")

    print("=" * 50)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())

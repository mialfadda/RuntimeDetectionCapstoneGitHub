"""
Test script to verify configuration setup
"""
import os
from config.config import DevelopmentConfig, ProductionConfig, TestingConfig


def test_configs():
    print("=" * 60)
    print("TESTING CONFIGURATION SETUP")
    print("=" * 60)

    # Test Development Config
    print("\n📘 DEVELOPMENT CONFIG:")
    dev = DevelopmentConfig()
    print(f"   Database: {dev.SQLALCHEMY_DATABASE_URI}")
    print(f"   Debug Mode: {dev.DEBUG}")
    print(f"   Rate Limit/min: {dev.RATE_LIMIT_PER_MINUTE}")
    print(f"   Model Path: {dev.PRIMARY_MODEL_PATH}")
    print(f"   Log Level: {dev.LOG_LEVEL}")

    # Test Production Config
    print("\n📗 PRODUCTION CONFIG:")
    prod = ProductionConfig()
    print(f"   Database: {prod.SQLALCHEMY_DATABASE_URI}")
    print(f"   Debug Mode: {prod.DEBUG}")
    print(f"   Rate Limit/min: {prod.RATE_LIMIT_PER_MINUTE}")
    print(f"   Session Secure: {prod.SESSION_COOKIE_SECURE}")

    # Test Testing Config
    print("\n📙 TESTING CONFIG:")
    test = TestingConfig()
    print(f"   Database: {test.SQLALCHEMY_DATABASE_URI}")
    print(f"   Testing Mode: {test.TESTING}")
    print(f"   Rate Limiting: {test.RATELIMIT_ENABLED}")

    # Check directories exist
    print("\n📁 CHECKING DIRECTORIES:")
    dirs = ['models', 'reports', 'logs']
    for dir_name in dirs:
        exists = "✅" if os.path.exists(dir_name) else "❌"
        print(f"   {exists} {dir_name}/")

    # Check .env file
    print("\n🔐 ENVIRONMENT FILE:")
    env_exists = "✅" if os.path.exists('.env') else "❌"
    print(f"   {env_exists} .env")

    print("\n" + "=" * 60)
    print("✅ CONFIGURATION TEST COMPLETE!")
    print("=" * 60)


if __name__ == '__main__':
    test_configs()
#!/usr/bin/env python3
"""
TenderWise Setup Script
Automated setup and configuration for TenderWise development environment.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import yaml
from typing import Dict, List, Optional

def print_banner():
    """Print setup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    TenderWise Setup                         ║
║                                                              ║
║  This script will help you set up TenderWise for            ║
║  development or production use.                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required.")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python version: {sys.version}")

def check_prerequisites():
    """Check for required system dependencies."""
    print("\n🔍 Checking prerequisites...")
    
    requirements = {
        "git": "Git version control",
        "docker": "Docker containerization (optional)",
        "sqlcmd": "SQL Server command line tools (optional)"
    }
    
    missing = []
    
    for cmd, description in requirements.items():
        if shutil.which(cmd):
            print(f"✅ {description}: Found")
        else:
            missing.append(f"⚠️  {description}: Not found")
    
    if missing:
        print("\nOptional dependencies not found:")
        for item in missing:
            print(f"   {item}")
        print("\nYou can continue without these, but some features may be limited.")
    
    return len(missing) == 0

def create_virtual_environment():
    """Create and activate virtual environment."""
    print("\n🔧 Setting up virtual environment...")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        response = input("Virtual environment already exists. Recreate? (y/N): ")
        if response.lower() == 'y':
            shutil.rmtree(venv_path)
        else:
            print("✅ Using existing virtual environment")
            return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        
        # Provide activation instructions
        if os.name == 'nt':  # Windows
            activate_cmd = r"venv\Scripts\activate"
        else:  # Unix/Linux/MacOS
            activate_cmd = "source venv/bin/activate"
        
        print(f"\n📝 To activate the virtual environment, run:")
        print(f"   {activate_cmd}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing dependencies...")
    
    # Determine pip command
    if os.name == 'nt':  # Windows
        pip_cmd = r"venv\Scripts\pip.exe"
    else:  # Unix/Linux/MacOS
        pip_cmd = "venv/bin/pip"
    
    if not Path(pip_cmd).exists():
        print("⚠️  Virtual environment not found. Please activate it manually and run:")
        print("   pip install -r requirements.txt")
        return False
    
    try:
        # Upgrade pip first
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment_file():
    """Set up environment configuration file."""
    print("\n⚙️  Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("✅ Using existing .env file")
            return True
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    # Copy example file
    shutil.copy(env_example, env_file)
    print("✅ Created .env file from template")
    
    # Prompt for key configuration values
    print("\n📝 Please configure the following required settings:")
    
    config_prompts = {
        "AZURE_AI_PROJECT_CONNECTION_STRING": "Azure AI Project connection string",
        "AZURE_AI_AGENT_ENDPOINT": "Azure AI Agent endpoint",
        "AZURE_AI_AGENT_API_KEY": "Azure AI Agent API key",
        "DATABASE_CONNECTION_STRING": "Database connection string"
    }
    
    env_content = env_file.read_text()
    
    for key, description in config_prompts.items():
        value = input(f"{description}: ").strip()
        if value:
            # Replace placeholder in .env file
            env_content = env_content.replace(f"{key}=your_", f"{key}={value}")
    
    env_file.write_text(env_content)
    
    print("✅ Environment configuration updated")
    print("💡 You can edit .env file later to add more configuration")
    
    return True

def setup_database():
    """Set up database."""
    print("\n🗄️  Database setup...")
    
    choice = input("Do you want to set up the database now? (y/N): ").strip().lower()
    
    if choice != 'y':
        print("⏭️  Skipping database setup")
        print("💡 You can run sql/create_database.sql manually later")
        return True
    
    db_type = input("Database type (1: SQL Server, 2: Docker SQL Server): ").strip()
    
    if db_type == "2":
        # Docker SQL Server setup
        return setup_docker_database()
    elif db_type == "1":
        # Existing SQL Server setup
        return setup_existing_database()
    else:
        print("⏭️  Skipping database setup")
        return True

def setup_docker_database():
    """Set up database using Docker."""
    if not shutil.which("docker"):
        print("❌ Docker not found. Please install Docker first.")
        return False
    
    try:
        print("🐳 Starting SQL Server container...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", "tenderwise-sql",
            "-e", "ACCEPT_EULA=Y",
            "-e", "SA_PASSWORD=TenderWise2024!",
            "-e", "MSSQL_PID=Developer",
            "-p", "1433:1433",
            "mcr.microsoft.com/mssql/server:2022-latest"
        ], check=True)
        
        print("✅ SQL Server container started")
        print("📝 Connection details:")
        print("   Server: localhost,1433")
        print("   Username: sa")
        print("   Password: TenderWise2024!")
        
        # Wait a bit for SQL Server to start
        print("⏳ Waiting for SQL Server to initialize...")
        import time
        time.sleep(10)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start SQL Server container: {e}")
        return False

def setup_existing_database():
    """Set up database on existing SQL Server."""
    print("📝 To set up the database manually:")
    print("   1. Connect to your SQL Server")
    print("   2. Create database: CREATE DATABASE TenderWiseDB;")
    print("   3. Run script: sql/create_database.sql")
    print("   4. Run additional procedures: sql/stored_procedures.sql")
    
    return True

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "uploads",
        "reports", 
        "logs",
        "scripts",
        "docs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_development_tools():
    """Set up development tools and configuration."""
    print("\n🛠️  Setting up development tools...")
    
    # Create VS Code settings if not exists
    vscode_dir = Path(".vscode")
    if not vscode_dir.exists():
        vscode_dir.mkdir()
        
        # Create basic VS Code settings
        settings = {
            "python.defaultInterpreterPath": "./venv/bin/python",
            "python.linting.enabled": True,
            "python.linting.pylintEnabled": False,
            "python.linting.flake8Enabled": True,
            "python.formatting.provider": "black",
            "python.testing.pytestEnabled": True,
            "python.testing.pytestArgs": ["tests"]
        }
        
        (vscode_dir / "settings.json").write_text(json.dumps(settings, indent=2))
        print("✅ Created VS Code settings")

def validate_setup():
    """Validate the setup by running basic checks."""
    print("\n✅ Validating setup...")
    
    checks = [
        ("Virtual environment", Path("venv").exists()),
        ("Environment file", Path(".env").exists()),
        ("Requirements installed", True),  # Assume installed if we got here
        ("Upload directory", Path("uploads").exists()),
        ("Reports directory", Path("reports").exists()),
        ("Logs directory", Path("logs").exists())
    ]
    
    all_good = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
        if not result:
            all_good = False
    
    return all_good

def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("   1. Activate virtual environment:")
    
    if os.name == 'nt':  # Windows
        print("      venv\\Scripts\\activate")
    else:  # Unix/Linux/MacOS
        print("      source venv/bin/activate")
    
    print("   2. Configure your .env file with actual credentials")
    print("   3. Set up your database using the SQL scripts")
    print("   4. Test the installation:")
    print("      python main.py cli")
    print("   5. Start the API server:")
    print("      python main.py")
    print("   6. Visit http://localhost:8000/docs for API documentation")
    
    print("\n📚 Additional resources:")
    print("   - README.md: Complete documentation")
    print("   - requirements.txt: Dependency list")
    print("   - .env.example: Configuration template")
    print("   - sql/: Database scripts")
    print("   - tests/: Test suite")

def main():
    """Main setup function."""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Check prerequisites
    check_prerequisites()
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Setup failed at virtual environment creation")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Set up environment file
    if not setup_environment_file():
        print("❌ Setup failed at environment configuration")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Set up development tools
    setup_development_tools()
    
    # Set up database
    setup_database()
    
    # Validate setup
    if validate_setup():
        print_next_steps()
    else:
        print("⚠️  Setup completed with some issues. Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        sys.exit(1)
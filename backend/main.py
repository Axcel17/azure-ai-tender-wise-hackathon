"""TenderWise - Intelligent Tender Document Analysis System
Main application entry point."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
try:
    from config.settings import get_settings, create_directories, validate_settings
    from api.main import app
    import uvicorn
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)

def setup_logging():
    """Setup application logging."""
    import logging
    from datetime import datetime
    
    settings = get_settings()
    
    # Create logs directory
    log_dir = Path(settings.log_file_path).parent
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("TenderWise")
    logger.info(f"🚀 TenderWise logging initialized - Level: {settings.log_level}")
    
    return logger

def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                         TenderWise                          ║
║              Intelligent Tender Analysis System             ║
║                                                              ║
║  🔍 Automated document analysis                              ║
║  ⚖️  LOSNCP compliance validation                           ║
║  🔗 RUC verification and contractor assessment              ║
║  📊 Comprehensive risk assessment                           ║
║  📋 Multi-proposal comparison                               ║
║  📄 Executive report generation                             ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check that required dependencies are available."""
    required_packages = [
        ("azure.ai.projects", "Azure AI Projects SDK"),
        ("semantic_kernel", "Microsoft Semantic Kernel"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn ASGI server"),
        ("pyodbc", "SQL Server ODBC driver"),
        ("PyPDF2", "PDF processing (optional)"),
        ("python-docx", "Word document processing (optional)")
    ]
    
    missing_packages = []
    
    for package_name, description in required_packages:
        try:
            __import__(package_name)
        except ImportError:
            if "optional" not in description:
                missing_packages.append(f"  - {package_name}: {description}")
    
    if missing_packages:
        print("❌ Missing required dependencies:")
        print("\n".join(missing_packages))
        print("\nPlease install missing packages and try again.")
        return False
    
    print("✅ All required dependencies are available")
    return True

def check_environment():
    """Check environment configuration."""
    settings = get_settings()
    
    print("🔧 Checking environment configuration...")
    
    # Check critical settings
    checks = [
        ("Azure AI Project", bool(settings.azure_ai_project_connection_string or 
                                 (settings.azure_ai_subscription_id and settings.azure_ai_resource_group))),
        ("Database", bool(settings.database_connection_string or 
                         (settings.database_server and settings.database_name))),
        ("Upload Directory", os.access(settings.upload_directory, os.W_OK) if os.path.exists(settings.upload_directory) else True),
        ("Reports Directory", os.access(settings.reports_directory, os.W_OK) if os.path.exists(settings.reports_directory) else True)
    ]
    
    all_good = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"  {status} {check_name}")
        if not check_result:
            all_good = False
    
    if not all_good:
        print("\n⚠️  Some environment checks failed. Please review your configuration.")
        print("   Check your .env file or environment variables.")
        return False
    
    return True

async def initialize_system():
    """Initialize the TenderWise system."""
    print("🔧 Initializing TenderWise system...")
    
    try:
        # Create necessary directories
        create_directories()
        
        # Validate settings
        validate_settings()
        
        print("✅ System initialization completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False

def run_api_server():
    """Run the FastAPI server."""
    settings = get_settings()
    
    print("🚀 Starting TenderWise API server...")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"   Debug mode: {settings.debug}")
    print(f"   Host: 0.0.0.0")
    print(f"   Port: 8000")
    print(f"   API Documentation: http://localhost:8000/docs")
    print()
    
    # Run the server
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )

def run_cli_mode():
    """Run in CLI mode for development and testing."""
    print("🔧 Running in CLI mode...")
    print("Available commands:")
    print("  1. Test document extraction")
    print("  2. Test compliance validation")
    print("  3. Test RUC validation") 
    print("  4. Test risk assessment")
    print("  5. Run comprehensive analysis")
    print("  6. Start API server")
    print("  0. Exit")
    
    while True:
        try:
            choice = input("\nEnter command (0-6): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                asyncio.run(test_document_extraction())
            elif choice == "2":
                asyncio.run(test_compliance_validation())
            elif choice == "3":
                asyncio.run(test_ruc_validation())
            elif choice == "4":
                asyncio.run(test_risk_assessment())
            elif choice == "5":
                asyncio.run(test_comprehensive_analysis())
            elif choice == "6":
                run_api_server()
                break
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_document_extraction():
    """Test document extraction functionality."""
    print("🔍 Testing document extraction...")
    
    # This would implement a test of the document extraction
    file_path = input("Enter path to test PDF file (or press Enter to skip): ").strip()
    
    if file_path and os.path.exists(file_path):
        try:
            from utils.document_utils import prepare_document_for_analysis
            
            print(f"📄 Analyzing document: {file_path}")
            document_info = await prepare_document_for_analysis(file_path)
            
            print(f"✅ Document analyzed successfully!")
            print(f"   Document type: {document_info['document_type']}")
            print(f"   Text length: {document_info['text_length']} characters")
            print(f"   Sections found: {len(document_info['sections'])}")
            print(f"   Entities found: {sum(len(v) for v in document_info['entities'].values())}")
            
        except Exception as e:
            print(f"❌ Document analysis failed: {e}")
    else:
        print("⚠️  No valid file provided or file not found")

async def test_compliance_validation():
    """Test compliance validation functionality."""
    print("⚖️  Testing compliance validation...")
    print("This would test LOSNCP compliance validation")

async def test_ruc_validation():
    """Test RUC validation functionality."""
    print("🔗 Testing RUC validation...")
    
    ruc = input("Enter RUC to validate (or press Enter to skip): ").strip()
    
    if ruc:
        try:
            from plugins.ruc_validation_plugin import RucValidationPlugin
            
            plugin = RucValidationPlugin()
            result = plugin.validate_ruc_format(ruc)
            
            print("✅ RUC validation completed:")
            print(result)
            
        except Exception as e:
            print(f"❌ RUC validation failed: {e}")
    else:
        print("⚠️  No RUC provided")

async def test_risk_assessment():
    """Test risk assessment functionality."""
    print("📊 Testing risk assessment...")
    print("This would test contract risk assessment")

async def test_comprehensive_analysis():
    """Test comprehensive analysis workflow."""
    print("📋 Testing comprehensive analysis...")
    print("This would run a full analysis workflow")

def main():
    """Main application entry point."""
    # Print banner
    print_banner()
    
    # Setup logging
    logger = setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n⚠️  Environment check warnings detected.")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("👋 Exiting. Please fix configuration issues and try again.")
            sys.exit(1)
    
    # Initialize system
    if not asyncio.run(initialize_system()):
        sys.exit(1)
    
    # Determine run mode
    run_mode = os.getenv("TENDERWISE_MODE", "api").lower()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "cli":
            run_mode = "cli"
        elif sys.argv[1] == "api":
            run_mode = "api"
    
    # Run in appropriate mode
    if run_mode == "cli":
        run_cli_mode()
    else:
        try:
            run_api_server()
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
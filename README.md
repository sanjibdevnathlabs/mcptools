# MCP Tools

A collection of production-grade Model Context Protocol (MCP) servers for various use cases.

## 📁 Project Structure

This repository contains multiple self-contained MCP server applications, each in its own directory:

### 🗃️ Database MCP Server (`database/`)

A production-grade MCP server for MySQL database interactions with enterprise-level security, monitoring, and schema management capabilities.

**Features:**
- Secure SQL execution with comprehensive parameter binding and validation
- Dual transport support (stdio and Server-Sent Events)
- Advanced security with SQL injection prevention and threat monitoring
- Production monitoring with health checks, metrics, and error tracking
- Intelligent error handling with retry logic and circuit breakers
- Advanced schema management with introspection and analysis
- Complete documentation and deployment guides

**Quick Start:**
```bash
cd database/
# Follow the README.md in the database directory for complete setup instructions
```

📖 **[Read the Database MCP Server Documentation →](database/README.md)**

## 🚀 Getting Started

Each directory contains a complete, self-contained MCP server application with:
- Full source code and configuration
- Comprehensive documentation
- Installation and deployment guides
- Usage examples and API reference

Choose the MCP server that fits your needs and follow the documentation in that directory.

## 🛠️ Development

Each MCP server is designed to be:
- **Self-contained**: All code, documentation, and configuration in one directory
- **Production-ready**: Enterprise-grade security, monitoring, and error handling
- **Well-documented**: Complete guides for installation, configuration, and deployment
- **Extensible**: Modular architecture for easy customization and extension

## 📋 Requirements

- Python 3.8+
- Virtual environment (recommended)
- Specific requirements vary by MCP server (see individual directories)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch for the specific MCP server you're working on
3. Make your changes in the appropriate directory
4. Follow the existing code style and documentation patterns
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Each MCP server is a complete, production-ready solution. Start with the one that matches your use case!**

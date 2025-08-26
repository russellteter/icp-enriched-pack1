# ICP Discovery Engine

AI-powered discovery engine for finding ideal customer prospects across Healthcare, Corporate, and Training sectors.

## 🚀 Quick Start

### 1. Start the Backend Server
```bash
make run
# OR: uvicorn src.server.app:app --port 8080 --reload
```

### 2. Launch the Modern UI (Default)
```bash
make ui
# OR: python launch_dashboard.py
```

Visit **http://localhost:8501** to access the clean, modern interface.

## 🎯 Modern UI Interface

The default interface provides a streamlined, user-friendly experience:

- **Home Screen**: Clear value proposition with single "Start Discovery" button
- **3-Step Setup Wizard**: Simple configuration (target → scope → confirm)
- **Progress Tracking**: Real-time updates with estimated completion time  
- **Clean Results**: Focused dashboard with export capabilities

### Alternative: Legacy Dashboard
For the complex multi-tab interface:
```bash
make ui-legacy
# OR: python launch_legacy_dashboard.py
```

## 📋 Available Commands

### Core Operations
- `make run` - Start FastAPI backend server on port 8080
- `make ui` - Launch modern UI interface (recommended)
- `make ui-legacy` - Launch legacy multi-tab dashboard
- `make ui-test` - Test modern UI components

### Development
- `make eval` - Run evaluation pipeline on latest results
- `make test` - Run pytest test suite  
- `make fmt` - Format code with ruff and black
- `make clean` - Clean cache and build artifacts

### System Monitoring
- `make system-health` - Check runtime health metrics
- `make cache-stats` - View cache performance
- `make batch-status` - Monitor batch processing

## 🎨 User Experience

### Modern UI Flow:
1. **Welcome** → Clear value proposition
2. **Setup** → 3 simple steps with smart defaults
3. **Progress** → Elegant tracking with time estimates  
4. **Results** → Clean dashboard with export options

### Key Features:
- **Single-purpose screens** - No confusing tabs
- **Progressive disclosure** - One decision at a time
- **Mobile responsive** - Works on any device
- **Clean design** - Modern purple theme (#4739E7)

## 🏗️ Architecture

### Backend (Port 8080)
- **FastAPI server** - REST API with health/metrics endpoints
- **LangGraph workflows** - Stateful discovery processes
- **MCP-style tools** - Web search, data enrichment, sheets integration
- **Budget management** - Cost controls and caching

### Frontend (Port 8501)  
- **Modern UI** - Streamlit-based clean interface (default)
- **Legacy Dashboard** - Complex multi-tab interface (backup)
- **API Integration** - Structured backend communication
- **Real-time updates** - Progress tracking and status

## 📊 Discovery Segments

### Healthcare EHR & Training
- Provider organizations with active EHR systems
- VILT training programs and lifecycle management
- Hospitals, clinics, health systems

### Corporate Learning Academies  
- Large enterprises (7,500+ employees)
- Named learning academies and training programs
- Fortune 1000 companies with structured L&D

### Professional Training Providers
- B2B training companies with live virtual instruction
- Training consultancies and certification providers
- Public calendar and course offerings

## 🛠️ Development Setup

### Prerequisites
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make install-deps
```

### Environment Configuration
1. Copy `.env.example` to `.env`
2. Configure budget limits and cache settings
3. Add any API keys for external services

### File Structure
```
src/
├── server/app.py          # FastAPI backend server
├── flows/                 # LangGraph discovery workflows  
├── tools/                 # MCP-style I/O tools
├── ui/
│   ├── modern_app.py     # Modern clean interface (default)
│   ├── dashboard.py      # Legacy multi-tab interface
│   ├── screens/          # Modern UI screens
│   └── components/       # Reusable UI components
evals/                     # Evaluation pipeline
docs/                      # Documentation and schemas
```

## 📈 Production Deployment

The system supports multiple deployment platforms:

- **Railway** (recommended): `railway init && railway up`
- **Render**: Connect GitHub repo, configure Python service  
- **Docker**: `make build && make docker-run`
- **Heroku**: Standard Python buildpack deployment

See `docs/DEPLOYMENT_GUIDE.md` for detailed instructions.

## 🧪 Testing & Validation

### UI Testing
```bash
make ui-test  # Test modern UI components
```

### Backend Testing  
```bash
make eval     # Run evaluation pipeline
make test     # Run pytest suite
```

### Quality Gates
- Schema validation (100% pass rate required)
- Tier mapping accuracy (100% required)  
- Evidence support (≥90% required)
- Geographic accuracy validation

## 📚 Documentation

- **CLAUDE.md** - Development guidelines and patterns
- **docs/PRD_enriched.md** - Product requirements
- **docs/schemas/** - Output schema definitions
- **docs/scoring/SCORING.md** - Quality scoring matrices

## 🎯 Getting Started

1. **Clone repository**
2. **Install dependencies**: `make install-deps`
3. **Start backend**: `make run`  
4. **Launch modern UI**: `make ui`
5. **Visit http://localhost:8501**
6. **Click "Start Discovery"** and follow the 3-step wizard

The modern interface guides you through the entire process without confusion or complexity.

---

**Modern UI is now the default interface** - clean, fast, and user-friendly. Use `make ui-legacy` if you need the complex multi-tab dashboard.
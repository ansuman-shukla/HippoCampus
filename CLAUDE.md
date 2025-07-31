# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (FastAPI + Python)
- **Start backend**: `cd backend ; uvicorn app.main:app --reload` (runs on port 8000)
- **Install dependencies**: `cd backend ; pip install -r requirements.txt`
- **Test rate limiting**: `cd backend ; python test_rate_limits_authenticated.py`
- **Comprehensive testing**: `cd backend ; python test_comprehensive_rate_limits.py`

### Frontend (React + TypeScript + Vite)
- **Development server**: `cd frontend ; npm run dev` (runs on port 5173)
- **Build for production**: `cd frontend ; npm run build`
- **Build without env replacement**: `cd frontend ; npm run build:base`
- **Lint code**: `cd frontend ; npm run lint`
- **Preview production build**: `cd frontend ; npm run preview`
- **Install dependencies**: `cd frontend ; npm install`

## Architecture Overview

### Project Structure
This is a Chrome extension application with a full-stack architecture:

- **Frontend**: React + TypeScript + Vite application that builds to both a web app and Chrome extension
- **Backend**: FastAPI Python server with comprehensive authentication and rate limiting
- **Database**: MongoDB (via Motor async driver) + Pinecone vector database for semantic search
- **Authentication**: Supabase Auth with JWT tokens and refresh token rotation

### Key Components

#### Backend Architecture (`backend/`)
- **FastAPI app** with comprehensive middleware for auth, CORS, and rate limiting
- **Rate limiting** using SlowAPI with per-user, per-route tracking (detailed in `RATE_LIMITING.md`)
- **Authentication middleware** with automatic token refresh and cookie management
- **Modular router structure**:
  - `auth_router.py` - Authentication endpoints
  - `bookmarkRouters.py` - Bookmark CRUD operations
  - `notesRouter.py` - Notes management
  - `summaryRouter.py` - AI-powered content summarization
  - `get_quotes.py` - Daily quotes feature
- **Services layer** for business logic (memories, notes, Pinecone operations, summarization)
- **Database wrappers** for MongoDB and Pinecone with health check capabilities

#### Frontend Architecture (`frontend/`)
- **Chrome Extension manifest v3** with content scripts and background service worker
- **React application** that works both as web app and extension popup/sidebar
- **Authentication flow** integrated with Supabase and extension auth
- **Component structure**:
  - `pages/` - Main application pages (Search, Response, Summarize, etc.)
  - `components/` - Reusable UI components with consistent styling
  - `hooks/` - Custom React hooks for authentication and state management
  - `utils/` - API client, auth utilities, and helper functions

### Key Technologies
- **Backend**: FastAPI, Motor (MongoDB), Pinecone, LangChain, Google Generative AI, SlowAPI
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Framer Motion
- **Authentication**: Supabase Auth with custom JWT handling
- **Extension**: Chrome Extension API v3 with service worker architecture

### Rate Limiting System
The application implements comprehensive rate limiting:
- **Per-user tracking** using JWT token user_id extraction
- **Route-specific limits** (e.g., 10/min for bookmarks, 5/day for summaries)
- **Automatic 429 responses** with detailed error messages
- **In-memory storage** (easily upgradeable to Redis for scaling)

### Authentication Flow
1. **Extension auth** via Supabase hosted login page
2. **JWT token management** with automatic refresh token rotation
3. **Secure cookie handling** with httpOnly, secure, and sameSite settings
4. **User creation** automatic user record creation on first authentication
5. **Middleware authentication** on all protected routes with comprehensive error handling

### Environment Configuration
The application uses environment variables for configuration:
- **Backend**: Uses python-dotenv for loading .env files
- **Frontend**: Uses Vite environment variables with build-time replacement for extension scripts
- **Build process**: Custom script (`replace-env-vars.mjs`) injects environment variables into extension files

### Chrome Extension Features
- **Sidebar injection** on any website with Alt+M shortcut to open the extension.
- **Content script** for authentication flow handling
- **Background service worker** for persistent functionality
- **Cross-origin permissions** for backend API communication

## File Structure

```
hippoCampus/
├── .claude/                          # Claude AI configuration
├── .git/                            # Git repository data
├── .gitignore                       # Global gitignore
├── .pytest_cache/                   # Pytest cache
├── backend_logs.txt                 # Backend development logs
├── frontend_log.txt                 # Frontend development logs
├── CLAUDE.md                        # This documentation file
│
├── backend/                         # FastAPI Python Backend
│   ├── .env                        # Environment variables (not in repo)
│   ├── .gitignore                  # Backend-specific gitignore
│   ├── .pytest_cache/              # Backend pytest cache
│   ├── venv/                       # Python virtual environment
│   ├── requirements.txt            # Python dependencies
│   ├── README.md                   # Backend documentation
│   ├── RATE_LIMITING.md            # Rate limiting documentation
│   ├── quick_test.py               # Quick testing utility
│   ├── test_comprehensive_rate_limits.py  # Comprehensive rate limit tests
│   ├── test_rate_limits_authenticated.py  # Authenticated rate limit tests
│   ├── __pycache__/                # Python bytecode cache
│   ├── scripts/                    # Utility scripts
│   │
│   └── app/                        # Main application package
│       ├── main.py                 # FastAPI application entry point
│       ├── __pycache__/            # App bytecode cache
│       │
│       ├── core/                   # Core functionality
│       │   ├── config.py           # Configuration management
│       │   ├── database.py         # Database connection
│       │   ├── database_wrapper.py # Database wrapper utilities
│       │   ├── pineConeDB.py       # Pinecone database connection
│       │   ├── pinecone_wrapper.py # Pinecone wrapper utilities
│       │   ├── rate_limiter.py     # Rate limiting implementation
│       │   └── __pycache__/        # Core bytecode cache
│       │
│       ├── exceptions/             # Custom exception classes
│       │   ├── databaseExceptions.py     # Database-related exceptions
│       │   ├── deleteExceptions.py       # Delete operation exceptions
│       │   ├── global_exceptions.py      # Global exception handlers
│       │   ├── httpExceptionsSave.py     # HTTP save exceptions
│       │   ├── httpExceptionsSearch.py   # HTTP search exceptions
│       │   └── __pycache__/              # Exceptions bytecode cache
│       │
│       ├── middleware/             # FastAPI middleware
│       │   ├── authentication.py   # Authentication middleware
│       │   └── __pycache__/        # Middleware bytecode cache
│       │
│       ├── models/                 # Database models
│       │   ├── bookmarkModels.py   # Bookmark data models
│       │   ├── notesModel.py       # Notes data models
│       │   ├── user_model.py       # User data models
│       │   └── __pycache__/        # Models bytecode cache
│       │
│       ├── routers/                # API route handlers
│       │   ├── auth_router.py      # Authentication routes
│       │   ├── bookmarkRouters.py  # Bookmark CRUD routes
│       │   ├── get_quotes.py       # Daily quotes routes
│       │   ├── notesRouter.py      # Notes management routes
│       │   ├── summaryRouter.py    # AI summarization routes
│       │   └── __pycache__/        # Routers bytecode cache
│       │
│       ├── schema/                 # Pydantic schemas
│       │   ├── bookmarksSchema.py  # Bookmark validation schemas
│       │   ├── link_schema.py      # Link validation schemas
│       │   ├── notesSchema.py      # Notes validation schemas
│       │   ├── users_schema.py     # User validation schemas
│       │   └── __pycache__/        # Schema bytecode cache
│       │
│       ├── services/               # Business logic layer
│       │   ├── memories_service.py # Memory management service
│       │   ├── notes_service.py    # Notes business logic
│       │   ├── pinecone_service.py # Pinecone operations service
│       │   ├── quotesService.py    # Quotes business logic
│       │   ├── summariseService.py # AI summarization service
│       │   ├── user_service.py     # User management service
│       │   └── __pycache__/        # Services bytecode cache
│       │
│       └── utils/                  # Utility functions
│           ├── jwt.py              # JWT token utilities
│           ├── quotes_dict.py      # Quotes dictionary data
│           ├── site_name_extractor.py  # Website name extraction
│           ├── space_extractor.py  # Text space extraction
│           └── __pycache__/        # Utils bytecode cache
│
└── frontend/                       # React TypeScript Frontend
    ├── .env                        # Frontend environment variables (not in repo)
    ├── .gitignore                  # Frontend-specific gitignore
    ├── node_modules/               # npm dependencies
    ├── dist/                       # Built application output
    ├── package.json                # npm package configuration
    ├── package-lock.json           # npm dependency lock
    ├── README.md                   # Frontend documentation
    ├── index.html                  # Main HTML template
    ├── vite.config.ts              # Vite build configuration
    ├── tsconfig.json               # TypeScript configuration
    ├── tsconfig.app.json           # App-specific TypeScript config
    ├── tsconfig.node.json          # Node-specific TypeScript config
    ├── tailwind.config.js          # Tailwind CSS configuration
    ├── postcss.config.js           # PostCSS configuration
    ├── eslint.config.js            # ESLint configuration
    ├── trial.txt                   # Development notes
    ├── for_taggay.zip              # Archive file
    ├── hippocampus_dict.zip        # Dictionary archive
    │
    ├── public/                     # Public static assets
    │   ├── manifest.json           # Chrome extension manifest
    │   ├── background.js           # Extension background script
    │   ├── content.js              # Extension content script
    │   ├── auth-content-script.js  # Authentication content script
    │   ├── content.css             # Content script styles
    │   ├── index.html              # Extension popup HTML
    │   ├── error.html              # Error page
    │   ├── HippoCampusLogo.png     # Application logo
    │   └── vite.svg                # Vite logo
    │
    ├── scripts/                    # Build and utility scripts
    │   └── replace-env-vars.mjs    # Environment variable injection script
    │
    └── src/                        # Source code
        ├── main.tsx                # React application entry point
        ├── App.tsx                 # Main React component
        ├── App.css                 # Application styles
        ├── index.css               # Global styles
        ├── vite-env.d.ts           # Vite type definitions
        ├── supabaseClient.ts       # Supabase client configuration
        │
        ├── assets/                 # Static assets (images, icons, etc.)
        ├── components/             # Reusable React components
        ├── config/                 # Configuration files
        ├── hooks/                  # Custom React hooks
        ├── page/                   # Page components
        └── utils/                  # Utility functions and helpers
```

## Development Notes
- The application is designed as a Chrome extension first, with web app capabilities
- Rate limiting is thoroughly implemented and documented in `RATE_LIMITING.md`
- Authentication uses a sophisticated token refresh system with concurrency control
- The build process includes environment variable injection for extension compatibility
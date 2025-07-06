# Dependency Management Guide for Multi-Agent System

## Overview
This guide ensures consistent dependency versions and compatibility across all generated applications.

## Backend Dependencies

### Core Requirements
```txt
# API Framework
fastapi==0.104.1
uvicorn[standard]==0.25.0

# AI Integration
anthropic==0.39.0

# Data Access
snowflake-connector-python==3.6.0
pandas==2.1.4
numpy==1.26.2

# Streaming
sse-starlette==1.8.2

# Utilities
python-dotenv==1.0.0
pydantic==2.5.3
httpx==0.25.2

# Security
PyJWT==2.8.0
cryptography==41.0.7
```

### Installation Command
```bash
pip install -r requirements.txt
```

## Frontend Dependencies

### Core Requirements
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2",
    "recharts": "^2.10.0",
    "react-markdown": "^9.0.1",
    "lucide-react": "^0.294.0",
    "@babel/standalone": "^7.23.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "eslint": "^8.55.0",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0"
  }
}
```

### Critical Version Notes

1. **Tailwind CSS**: Use v3.x.x, NOT v4.x.x
   - v4 has breaking changes in utility classes
   - v3 supports all glassmorphism effects needed

2. **React**: Use v18.x.x
   - Ensure proper createRoot usage
   - Support for concurrent features

3. **Vite**: Use v5.x.x
   - Faster builds
   - Better TypeScript support

4. **TypeScript**: Use v5.x.x
   - Better type inference
   - Improved module resolution

## Common Issues & Solutions

### Issue: Tailwind CSS v4 Incompatibility
**Symptom**: `backdrop-blur-md` not recognized
**Solution**: 
```bash
npm uninstall tailwindcss @tailwindcss/postcss
npm install -D tailwindcss@^3 postcss autoprefixer
```

### Issue: TypeScript Module Resolution
**Symptom**: "does not provide an export named"
**Solution**: Use explicit type imports
```typescript
// Instead of:
import { SpecialistStatus, SPECIALIST_COLORS } from './types';

// Use:
import type { SpecialistStatus } from './types';
import { SPECIALIST_COLORS } from './types';
```

### Issue: SSE Connection Method
**Symptom**: 405 Method Not Allowed on POST
**Solution**: Use EventSource properly
```typescript
// Correct SSE implementation
const eventSource = new EventSource(
  `/api/chat/stream?message=${encodeURIComponent(message)}`
);
```

### Issue: Dynamic Code Execution
**Symptom**: Visualizations don't render
**Solution**: Ensure @babel/standalone is installed
```bash
npm install @babel/standalone
```

## Environment Setup

### Backend .env Template
```env
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Snowflake (if using real data)
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/key.pem
SNOWFLAKE_DATABASE=your_db
SNOWFLAKE_SCHEMA=your_schema

# Optional
LOG_LEVEL=INFO
MAX_WORKERS=4
```

### Frontend Environment Variables
```env
# .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_SSE_RECONNECT_TIMEOUT=3000
```

## Version Lock File

Always commit lock files:
- Backend: `requirements.txt` with pinned versions
- Frontend: `package-lock.json` or `yarn.lock`

This ensures reproducible builds across environments.

## Testing Compatibility

Before deployment, verify:

1. **Backend Tests**
```bash
python -m pytest tests/
```

2. **Frontend Tests**
```bash
npm run test
npm run build
```

3. **Integration Tests**
```bash
# Start both services
# Run integration test suite
npm run test:e2e
```

## Update Strategy

1. **Minor Updates**: Safe within same major version
2. **Major Updates**: Test thoroughly in staging
3. **Security Updates**: Apply immediately after testing

## Troubleshooting Checklist

- [ ] Correct Python version (3.11+)
- [ ] Correct Node version (18+)
- [ ] All dependencies installed
- [ ] Environment variables set
- [ ] No version conflicts
- [ ] Lock files committed
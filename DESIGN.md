# Predictions Platform Design Specification

## Overview

A personal predictions tracking platform designed to capture the Platonic ideal of what a forecasting tool should be. Built as a multi-user platform with TypeScript/Vercel, providing both a REST API and MCP (Model Context Protocol) integration.

### Goals

- Enable users to track predictions across multiple question types (binary, range, multi-choice)
- Maintain detailed forecast history over time
- Support resolution and calibration tracking
- Provide seamless Claude integration via MCP
- Allow import from existing platforms (Fatebook, Metaculus)
- Support generic export for data portability

### Non-Goals (v1)

- Prediction markets / monetary components
- Real-time collaboration features
- Complex social networking features
- Mobile-specific features
- Sync between multiple instances

## Architecture Overview

```
┌─────────────────┐
│   Claude via    │
│   MCP Server    │
└────────┬────────┘
         │
         │ MCP Protocol
         │
┌────────▼────────┐
│  MCP Server     │
│  (TypeScript)   │
└────────┬────────┘
         │
         │ REST API
         │
┌────────▼────────┐     ┌──────────────┐
│   Backend API   │────▶│   Database   │
│   (Vercel)      │     │  (Postgres)  │
└────────┬────────┘     └──────────────┘
         │
         │
┌────────▼────────┐
│  Web UI         │
│  (Optional)     │
└─────────────────┘
```

### Technology Stack

- **Backend**: TypeScript on Vercel (serverless functions or Next.js API routes)
- **Database**: Hosted Postgres (Vercel Postgres, Supabase, or Neon)
- **MCP Server**: TypeScript (can run locally or deployed)
- **Authentication**: JWT-based, API keys for programmatic access
- **API Style**: REST (with potential GraphQL later)

## Data Model

### Core Entities

#### User

```typescript
interface User {
  id: string;                    // UUID
  email: string;                 // Unique
  username: string;              // Unique, display name
  passwordHash: string;          // bcrypt
  createdAt: Date;
  updatedAt: Date;

  // Settings
  defaultVisibility: VisibilityLevel;
  timezone: string;

  // Stats (computed)
  totalPredictions?: number;
  totalForecasts?: number;
  calibrationScore?: number;
}
```

#### ApiKey

```typescript
interface ApiKey {
  id: string;                    // UUID
  userId: string;                // Foreign key
  key: string;                   // Hashed, for MCP/API access
  name: string;                  // User-defined label
  createdAt: Date;
  lastUsedAt?: Date;
  expiresAt?: Date;
  scopes: string[];              // e.g., ["read", "write"]
}
```

#### Prediction

Base prediction with discriminated union for question types:

```typescript
type Prediction =
  | BinaryPrediction
  | RangePrediction
  | MultiChoicePrediction;

interface BasePrediction {
  id: string;                    // UUID
  userId: string;                // Foreign key (creator)

  // Content
  title: string;                 // The question
  description?: string;          // Markdown notes/context

  // Temporal
  createdAt: Date;
  updatedAt: Date;
  resolveBy: Date;               // Expected resolution date
  resolvedAt?: Date;             // Actual resolution date
  hideForecastsUntil?: Date;     // Optional blind period

  // Organization
  tags: string[];                // User-defined tags
  category?: string;             // Optional category

  // Visibility
  visibility: Visibility;

  // Resolution
  resolution?: Resolution;

  // Metadata
  source?: string;               // e.g., "imported:fatebook"
  externalId?: string;           // Original ID if imported
}

interface BinaryPrediction extends BasePrediction {
  type: "binary";
  // No additional fields needed
}

interface RangePrediction extends BasePrediction {
  type: "range";
  rangeMin: number;              // Minimum possible value
  rangeMax: number;              // Maximum possible value
  unit?: string;                 // e.g., "meters", "dollars"
}

interface MultiChoicePrediction extends BasePrediction {
  type: "multi_choice";
  options: PredictionOption[];
}

interface PredictionOption {
  id: string;                    // UUID
  text: string;
  createdAt: Date;
}
```

#### Visibility

```typescript
interface Visibility {
  level: VisibilityLevel;
  sharedWith?: ShareTarget[];    // Only relevant if level is "shared"
}

type VisibilityLevel = "private" | "public" | "unlisted" | "shared";

interface ShareTarget {
  type: "user" | "group";        // "group" for future expansion
  id: string;                    // User ID or group ID
}
```

#### Forecast

Represents a prediction at a point in time:

```typescript
type Forecast =
  | BinaryForecast
  | RangeForecast
  | MultiChoiceForecast;

interface BaseForecast {
  id: string;                    // UUID
  predictionId: string;          // Foreign key
  userId: string;                // Who made the forecast
  createdAt: Date;
  reasoning?: string;            // Optional notes
}

interface BinaryForecast extends BaseForecast {
  type: "binary";
  probability: number;           // 0-1
}

interface RangeForecast extends BaseForecast {
  type: "range";
  forecastMin: number;           // Lower bound
  forecastMax: number;           // Upper bound
  confidenceLevel: number;       // e.g., 0.8 for 80% credible interval
  pointEstimate?: number;        // Optional central estimate
}

interface MultiChoiceForecast extends BaseForecast {
  type: "multi_choice";
  probabilities: Record<string, number>;  // optionId -> probability (must sum to 1)
}
```

#### Resolution

```typescript
type Resolution =
  | BinaryResolution
  | RangeResolution
  | MultiChoiceResolution
  | CancelledResolution;

interface BaseResolution {
  resolvedAt: Date;
  resolvedBy: string;            // User ID
  notes?: string;                // Reasoning for resolution
}

interface BinaryResolution extends BaseResolution {
  type: "binary";
  outcome: "yes" | "no" | "ambiguous";
}

interface RangeResolution extends BaseResolution {
  type: "range";
  value: number;                 // Actual outcome value
}

interface MultiChoiceResolution extends BaseResolution {
  type: "multi_choice";
  selectedOptionId: string;
}

interface CancelledResolution extends BaseResolution {
  type: "cancelled";
  reason: string;                // Why was it cancelled
}
```

#### Comment

```typescript
interface Comment {
  id: string;                    // UUID
  predictionId: string;          // Foreign key
  userId: string;                // Foreign key
  content: string;               // Markdown
  createdAt: Date;
  updatedAt: Date;
  parentId?: string;             // For threaded comments (future)
}
```

### Database Schema Considerations

**Relationships:**
- User → Predictions (one-to-many)
- User → Forecasts (one-to-many)
- User → Comments (one-to-many)
- User → ApiKeys (one-to-many)
- Prediction → Forecasts (one-to-many)
- Prediction → Comments (one-to-many)
- Prediction → PredictionOptions (one-to-many, for multi-choice)

**Indexes:**
- User: email, username
- Prediction: userId, createdAt, resolveBy, tags (GIN), visibility
- Forecast: predictionId, userId, createdAt
- Comment: predictionId, userId, createdAt
- ApiKey: userId, key (hashed)

**Polymorphism Handling:**
For discriminated unions (Prediction, Forecast, Resolution), options:
1. **Single table with JSON columns** - Store type-specific data in JSONB
2. **Separate tables per type** - More normalized, complex joins
3. **Hybrid** - Common fields in main table, type-specific in related tables

Recommendation: **Single table with JSONB** for flexibility and simpler queries.

## API Design

### Authentication

Two authentication modes:

1. **JWT Tokens** (for web UI)
   - POST `/auth/login` - Get JWT
   - POST `/auth/register` - Create account
   - POST `/auth/refresh` - Refresh token

2. **API Keys** (for MCP/programmatic access)
   - Header: `Authorization: Bearer <api-key>`
   - POST `/api-keys` - Generate new key
   - GET `/api-keys` - List user's keys
   - DELETE `/api-keys/:id` - Revoke key

### Core Endpoints

#### Predictions

```typescript
// Create prediction
POST /predictions
Body: {
  type: "binary" | "range" | "multi_choice";
  title: string;
  description?: string;
  resolveBy: string;  // ISO 8601
  tags?: string[];
  visibility?: Visibility;

  // Type-specific
  rangeMin?: number;        // For range
  rangeMax?: number;        // For range
  unit?: string;            // For range
  options?: string[];       // For multi_choice

  // Initial forecast
  initialForecast?: {
    probability?: number;           // Binary
    forecastMin?: number;           // Range
    forecastMax?: number;           // Range
    confidenceLevel?: number;       // Range
    probabilities?: Record<string, number>;  // Multi-choice
    reasoning?: string;
  };
}

// List predictions
GET /predictions?
  resolved=true|false
  &userId=<uuid>           // Filter by creator
  &tag=<tag>               // Filter by tag (repeatable)
  &search=<query>          // Full-text search
  &limit=<number>
  &cursor=<cursor>         // Pagination

// Get single prediction
GET /predictions/:id
  ?includeForecasts=true   // Include forecast history
  &includeComments=true    // Include comments

// Update prediction
PATCH /predictions/:id
Body: {
  title?: string;
  description?: string;
  resolveBy?: string;
  tags?: string[];
  visibility?: Visibility;
}

// Delete prediction
DELETE /predictions/:id

// Resolve prediction
POST /predictions/:id/resolve
Body: {
  type: "binary" | "range" | "multi_choice" | "cancelled";

  // Type-specific
  outcome?: "yes" | "no" | "ambiguous";  // Binary
  value?: number;                         // Range
  selectedOptionId?: string;              // Multi-choice
  reason?: string;                        // Cancelled

  notes?: string;
  resolvedAt?: string;  // ISO 8601, defaults to now
}
```

#### Forecasts

```typescript
// Add forecast
POST /predictions/:id/forecasts
Body: {
  probability?: number;           // Binary
  forecastMin?: number;           // Range
  forecastMax?: number;           // Range
  confidenceLevel?: number;       // Range
  pointEstimate?: number;         // Range (optional)
  probabilities?: Record<string, number>;  // Multi-choice
  reasoning?: string;
}

// Get forecasts for a prediction
GET /predictions/:id/forecasts
  ?userId=<uuid>           // Filter to specific user

// Get user's forecast history
GET /users/:userId/forecasts
  ?limit=<number>
  &cursor=<cursor>
```

#### Comments

```typescript
// Add comment
POST /predictions/:id/comments
Body: {
  content: string;  // Markdown
}

// Get comments
GET /predictions/:id/comments
  ?limit=<number>
  &cursor=<cursor>

// Update comment
PATCH /comments/:id
Body: {
  content: string;
}

// Delete comment
DELETE /comments/:id
```

#### User & Stats

```typescript
// Get user profile
GET /users/:userId

// Get user stats
GET /users/:userId/stats
Response: {
  totalPredictions: number;
  totalForecasts: number;
  resolvedPredictions: number;

  // Calibration data
  calibrationByBucket: {
    bucket: string;        // e.g., "0-10%", "10-20%"
    predicted: number;     // Average prediction
    actual: number;        // Actual rate
    count: number;         // Sample size
  }[];

  brierScore?: number;
  logScore?: number;
}
```

### Error Handling

Standard HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad request (validation error)
- 401: Unauthorized
- 403: Forbidden (insufficient permissions)
- 404: Not found
- 409: Conflict (e.g., duplicate)
- 500: Internal server error

Error response format:
```typescript
{
  error: {
    code: string;          // Machine-readable error code
    message: string;       // Human-readable message
    details?: any;         // Additional context
  }
}
```

## Authorization Model

### Permissions

For v1, simple ownership model:
- Users can create predictions
- Users can add forecasts to any visible prediction
- Users can only edit/delete their own predictions and comments
- Users can see predictions based on visibility settings:
  - `private`: Only the creator
  - `public`: Anyone (including unauthenticated)
  - `unlisted`: Anyone with the link
  - `shared`: Creator and users in `sharedWith` list

### Future Extensions

- Groups/organizations
- Collaborative predictions (multiple owners)
- Moderator roles
- Public/private forecast options (hide forecast while contributing)

## Import/Export

### Import from Fatebook

```typescript
POST /import/fatebook
Body: {
  apiKey: string;          // User's Fatebook API key
  options?: {
    limit?: number;        // Max predictions to import
    visibility?: VisibilityLevel;  // Override visibility
    includeForecastHistory?: boolean;
  }
}

Response: {
  imported: number;
  skipped: number;
  errors: { questionId: string; error: string; }[];
}
```

**Mapping:**
- Fatebook question → Prediction
- Fatebook forecasts → Our forecasts
- Store original Fatebook ID in `externalId`
- Set `source: "imported:fatebook"`

### Import from Metaculus

```typescript
POST /import/metaculus
Body: {
  username: string;        // Metaculus username (public API)
  options?: {
    limit?: number;
    visibility?: VisibilityLevel;
  }
}
```

### Generic Export

```typescript
GET /export
  ?format=json|csv
  &includeForecasts=true
  &includeComments=true

// Returns downloadable file with all user's predictions
```

## MCP Integration

### MCP Server Architecture

The MCP server acts as a thin client over the backend API:

```typescript
// MCP Server config
{
  "backend_url": "https://predictions.yourapp.com",
  "api_key": "<user-api-key>"
}
```

### MCP Tools

Tools exposed via MCP:

1. **create_prediction** - Create new prediction
2. **get_predictions** - List predictions with filters
3. **get_prediction** - Get single prediction details
4. **add_forecast** - Add/update forecast
5. **resolve_prediction** - Resolve a prediction
6. **add_comment** - Comment on prediction
7. **update_prediction** - Update metadata
8. **delete_prediction** - Delete prediction
9. **import_fatebook** - Trigger Fatebook import
10. **get_user_stats** - Get calibration stats

Each tool maps directly to backend API calls.

### Configuration

Users configure MCP server in Claude Desktop:

```json
{
  "mcpServers": {
    "predictions": {
      "command": "npx",
      "args": ["-y", "predictions-mcp"],
      "env": {
        "PREDICTIONS_API_URL": "https://predictions.yourapp.com",
        "PREDICTIONS_API_KEY": "user-api-key-here"
      }
    }
  }
}
```

Or for local development:

```json
{
  "mcpServers": {
    "predictions": {
      "command": "npx",
      "args": ["-y", "predictions-mcp"],
      "env": {
        "PREDICTIONS_API_URL": "http://localhost:3000",
        "PREDICTIONS_API_KEY": "dev-api-key"
      }
    }
  }
}
```

## Deployment

### Vercel Deployment

**Project Structure:**
```
predictions-platform/
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   │   ├── predictions/
│   │   ├── forecasts/
│   │   ├── auth/
│   │   └── ...
│   └── (web)/             # Web UI (optional)
├── lib/
│   ├── db/                # Database client & migrations
│   ├── auth/              # Auth utilities
│   ├── validation/        # Request validation
│   └── types/             # Shared TypeScript types
├── prisma/
│   └── schema.prisma      # Database schema
└── package.json
```

**Database:**
- Use Vercel Postgres or external (Supabase/Neon)
- Prisma for ORM and migrations
- Connection pooling for serverless

**Environment Variables:**
```
DATABASE_URL=
JWT_SECRET=
NEXTAUTH_SECRET=
NEXTAUTH_URL=
```

### MCP Server Deployment

Two options:

1. **Local-only** (simpler for v1)
   - Users run MCP server locally via `npx`
   - Points to hosted backend API
   - No deployment needed for MCP server

2. **Remote MCP server** (future)
   - Deploy MCP server as separate service
   - Users configure SSE/WebSocket transport
   - More complex but better for web-based Claude

Recommend: **Start with local MCP server** pointing to hosted backend.

## Implementation Phases

### Phase 1: Minimal Viable Platform
1. Database schema & Prisma setup
2. User auth (register, login, API keys)
3. Binary predictions only
4. Create, list, get, forecast, resolve endpoints
5. Basic MCP server with core tools
6. Deploy to Vercel

### Phase 2: Full Prediction Types
1. Range predictions
2. Multi-choice predictions
3. Type-specific validation and UI

### Phase 3: Import & Stats
1. Fatebook import
2. Calibration calculation
3. Stats endpoints
4. Metaculus import (if needed)

### Phase 4: Polish
1. Comments system
2. Tags & search
3. Export functionality
4. Web UI (optional)

### Phase 5: Advanced Features
1. Shared predictions
2. Groups/organizations
3. Public prediction browsing
4. Advanced calibration visualizations

## Open Questions

1. **Web UI Priority**: Build alongside API or defer until API is stable?
2. **Real-time Updates**: WebSockets for live forecast updates, or polling sufficient?
3. **File Uploads**: Support images/attachments in descriptions/comments?
4. **Anonymity**: Option for anonymous public predictions?
5. **Scoring**: Which calibration metrics to prioritize? (Brier, log score, others?)
6. **Rate Limiting**: Strategy for API rate limits?
7. **Data Retention**: Soft delete vs hard delete? Archive old predictions?

## Success Metrics

**For v1:**
- Successfully import Fatebook predictions
- Create and resolve predictions via MCP
- View calibration stats
- API response time < 200ms p95
- Zero data loss

**Future:**
- Daily active users
- Predictions created per user
- Forecast update frequency
- Calibration score improvements over time

## References

- [Fatebook API](https://fatebook.io/api/openapi.json)
- [MCP Specification](https://modelcontextprotocol.io/llms-full.txt)
- [Vercel Deployment Docs](https://vercel.com/docs)

---

*Last Updated: 2025-12-29*

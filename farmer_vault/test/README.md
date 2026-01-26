# Frontend Testing

## Current Coverage

### ✅ Hooks
- `useGraph.test.ts` - SWR integration, fetch handling, caching

### 🚧 API Routes (Integration Tests)
API route tests are complex due to Node.js module mocking in Vitest.

**Current status:**
- Test infrastructure in place
- Mock setup needs refinement for fs/promises and child_process

**Recommendation:**
For MVP, rely on:
1. Manual testing via development server
2. Production build verification (TypeScript catches major issues)
3. End-to-end test in Task 16

API route unit tests can be expanded post-MVP.

## Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch
```

## Philosophy

Following project guidelines:
- **Tests on critical paths, not ceremony**
- Focus on hooks and components (user-facing logic)
- API routes verified through integration and manual testing

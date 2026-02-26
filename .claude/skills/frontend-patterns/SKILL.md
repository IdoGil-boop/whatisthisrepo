---
name: frontend-patterns
description: React and Next.js frontend patterns. Component architecture, hooks, state management, API integration, and Playwright E2E testing.
---

# Frontend Development Patterns

Frontend patterns for a React/Next.js application with TanStack Query.

## Component Patterns

### Composition Over Inheritance

```typescript
interface CardProps {
  children: React.ReactNode;
  variant?: "default" | "outlined";
}

export function Card({ children, variant = "default" }: CardProps) {
  return <div className={`card card-${variant}`}>{children}</div>;
}

export function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="card-header">{children}</div>;
}

// Usage
<Card variant="outlined">
  <CardHeader>Item Scores</CardHeader>
  <ScoreTable scores={scores} />
</Card>
```

### Typed Props with Defaults

```typescript
interface ItemCardProps {
  item: Item;
  onSelect: (id: number) => void;
  showDetails?: boolean;
}

export function ItemCard({
  item,
  onSelect,
  showDetails = false,
}: ItemCardProps) {
  return (
    <div onClick={() => onSelect(item.id)} className="cursor-pointer">
      <h3>{item.name}</h3>
      {showDetails && <ItemDetails item={item} />}
    </div>
  );
}
```

### Conditional Rendering

```typescript
// GOOD: Clear conditional rendering
{isLoading && <Spinner />}
{error && <ErrorMessage error={error} />}
{data && <DataDisplay data={data} />}

// BAD: Ternary nesting
{isLoading ? <Spinner /> : error ? <ErrorMessage /> : <DataDisplay />}
```

## State Management with TanStack Query

### Data Fetching

```typescript
import { useQuery } from "@tanstack/react-query";

function useItemRuns(itemId: number) {
  return useQuery({
    queryKey: ["item-runs", itemId],
    queryFn: () =>
      fetch(`/api/runs?item_id=${itemId}`).then((r) => r.json()),
    staleTime: 60 * 1000, // 1 minute
  });
}

// Usage in component
function RunsPage() {
  const { data: runs, isLoading, error } = useItemRuns(selectedItemId);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner error={error} />;
  return <RunsTable runs={runs} />;
}
```

### Mutations

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";

function useApproveItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: number) =>
      fetch(`/api/items/${itemId}/approve`, { method: "POST" }).then(
        (r) => r.json()
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] });
    },
  });
}
```

## Custom Hooks

### Debounce Hook

```typescript
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

// Usage
const debouncedQuery = useDebounce(searchQuery, 500);
```

### Toggle Hook

```typescript
export function useToggle(initial = false): [boolean, () => void] {
  const [value, setValue] = useState(initial);
  const toggle = useCallback(() => setValue((v) => !v), []);
  return [value, toggle];
}
```

## Performance Optimization

### Memoization

```typescript
// useMemo for expensive computations
const sortedScores = useMemo(
  () => scores.sort((a, b) => b.score - a.score),
  [scores]
);

// useCallback for functions passed to children
const handleSearch = useCallback((query: string) => {
  setSearchQuery(query);
}, []);

// React.memo for pure display components
export const ScoreRow = React.memo<ScoreRowProps>(({ score }) => (
  <tr>
    <td>{score.text}</td>
    <td>{score.score.toFixed(3)}</td>
  </tr>
));
```

### Code Splitting

```typescript
import { lazy, Suspense } from "react";

const AnalyticsChart = lazy(() => import("./AnalyticsChart"));

export function AnalyticsPage() {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <AnalyticsChart data={data} />
    </Suspense>
  );
}
```

## E2E Testing with Playwright

### Page Object Model Pattern

```typescript
import { Page, Locator, expect } from "@playwright/test";

export class ExamplePage {
  readonly page: Page;
  readonly heading: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.locator("h1", { hasText: "Example" });
  }

  async goto() {
    await this.page.goto("/example");
    await this.page.waitForLoadState("networkidle");
  }

  async waitForLoaded() {
    await expect(this.heading).toBeVisible({ timeout: 10_000 });
  }

  async screenshot(name: string) {
    await this.page.screenshot({
      path: `tests/e2e/artifacts/${name}.png`,
      fullPage: true,
    });
  }
}
```

### Running E2E Tests

```bash
npx playwright test
npx playwright test tests/e2e/example.spec.ts  # Single file
npx playwright test --headed                     # With browser UI
npx playwright show-report                       # View HTML report
```

## Error Boundaries

```typescript
"use client";

import { Component, ErrorInfo, ReactNode } from "react";

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Error boundary:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-4 text-red-400">
          <h2>Something went wrong</h2>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

---

**Remember**: Prioritize clarity, data density, and reliability over visual polish.

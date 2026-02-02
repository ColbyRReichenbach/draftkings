# Skill: React Dashboard

DraftKings design system and component patterns.

## Colors
```css
:root {
  --dk-green: #53B848;
  --dk-black: #000000;
  --dk-alert-orange: #F3701B;
  --dk-warning-yellow: #FFB81C;
}
```

## Risk Card Component
```typescript
export const RiskCaseCard: React.FC<{case: RiskCase}> = ({ case }) => {
  return (
    <div className="bg-white border-l-4 border-red-500 p-6 rounded-lg">
      <h3 className="font-bold text-lg">
        {case.risk_category} - {case.player_id}
      </h3>
      <p className="mt-2 text-gray-700">{case.ai_explanation}</p>
      
      <div className="mt-4 flex gap-2">
        <button className="px-4 py-2 bg-[#53B848] text-white rounded">
          Send Nudge
        </button>
      </div>
    </div>
  );
};
```

## Data Fetching
```typescript
import { useQuery } from '@tanstack/react-query';

export const useInterventionQueue = () => {
  return useQuery({
    queryKey: ['intervention-queue'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/queue');
      return res.json();
    },
    refetchInterval: 30000  // 30 seconds
  });
};
```

## Performance
- Use React.memo() for cards
- Virtualize lists >100 items
- Lazy load detail views
- Debounce filter inputs (300ms)

import { appendReplayTimelineEntry, getReplayTimelineEntries } from '../staticReplayTimeline';

describe('staticReplayTimeline', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('stores and returns replay entries for a player', () => {
    appendReplayTimelineEntry('PLR_1000_MA', {
      event_type: 'Auto Trigger Check (Replayed)',
      event_detail: 'MA: Not triggered',
      created_at: '2026-02-04T10:00:00Z',
      source: 'static_replay',
      ephemeral: true,
    });

    const entries = getReplayTimelineEntries('PLR_1000_MA');
    expect(entries).toHaveLength(1);
    expect(entries[0].source).toBe('static_replay');
  });

  it('caps replay entries per player to 20', () => {
    for (let i = 0; i < 25; i++) {
      appendReplayTimelineEntry('PLR_1001_NJ', {
        event_type: `Replay ${i}`,
        event_detail: `detail ${i}`,
        created_at: `2026-02-04T10:${String(i).padStart(2, '0')}:00Z`,
        source: 'static_replay',
        ephemeral: true,
      });
    }

    const entries = getReplayTimelineEntries('PLR_1001_NJ');
    expect(entries).toHaveLength(20);
    expect(entries[0].event_type).toBe('Replay 24');
    expect(entries[19].event_type).toBe('Replay 5');
  });
});

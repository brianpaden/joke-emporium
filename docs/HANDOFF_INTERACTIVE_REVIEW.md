# Interactive Review TUI (Terminal User Interface)

**Status:** Planning
**Priority:** P1 (Short-term)
**Effort:** 1 week
**Impact:** Transform manual review from tedious to efficient

## Problem Statement

Current `review` command is cumbersome:
- Shows limited joke info without verbose flags
- No pagination or navigation
- Must copy/paste staging IDs for actions
- No keyboard shortcuts
- Can't see progress or stats
- No undo functionality
- No filtering during review session

For reviewing 50,000+ jokes after policy automation, need better UX.

## Solution Overview

Build an interactive Terminal User Interface (TUI) using `textual` (modern Python TUI framework, already using `rich` for output). Provides spreadsheet-like experience with keyboard navigation, filters, and instant actions.

### Visual Mockup

```
┌─ Import Batch Review: abc-123 ─────────────────────────────────────────────┐
│ Progress: 234/1,250 (18.7%) │ Session: 45 approved, 12 rejected, 3 flagged │
├─────────────────────────────────────────────────────────────────────────────┤
│ Filters: [Maturity: All ▼] [Score: 0-100] [Flags: NSFW ▼] [Status: Pending]│
├─────────────────────────────────────────────────────────────────────────────┤
│ ID        │ Preview                       │ Score │ Mat │ Flags     │ Status│
├───────────┼───────────────────────────────┼───────┼─────┼───────────┼───────┤
│ ► stg_001 │ Why did the chicken cross... │  85.3 │  G  │ -         │ PEND  │
│   stg_002 │ A priest, a rabbi, and...    │  42.1 │  R  │ Religious │ PEND  │
│   stg_003 │ What's the difference...     │  91.2 │  G  │ -         │ PEND  │
│   stg_004 │ Yo mama so fat...            │  15.8 │  R  │ NSFW      │ PEND  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Selected: stg_001                                                            │
│ ┌── Full Content ─────────────────────────────────────────────────────────┐│
│ │ Setup: Why did the chicken cross the road?                              ││
│ │ Punchline: To get to the other side!                                    ││
│ │                                                                          ││
│ │ Categories: ANIMALS, WORDPLAY                                           ││
│ │ Structure: QUESTION_ANSWER                                              ││
│ │ Mechanisms: INCONGRUITY                                                 ││
│ │ Source: reddit.com/r/jokes (u/comedian123, 2023-05-15)                 ││
│ │ Ratings: Funniness 85.3/100 (12 votes), Quality 3.2/5                  ││
│ └──────────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│ [A]pprove [R]eject [F]lag [E]dit [S]kip [U]ndo [J/K]Nav [/]Filter [Q]uit │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Architecture

### Technology Stack

**Primary:** `textual` - Modern TUI framework
- Rich text rendering (already using `rich`)
- Reactive data tables
- Keyboard/mouse support
- Responsive layouts
- Built-in widgets (tables, modals, inputs)

**Alternative:** `urwid` (if textual too heavy)

### File Structure

```
src/joke_emporium/
├── importers/
│   ├── cli.py                    # MODIFY: Add review-interactive command
│   └── tui/                      # NEW: TUI components
│       ├── __init__.py
│       ├── app.py                # Main Textual app
│       ├── widgets/
│       │   ├── joke_table.py     # Paginated joke table
│       │   ├── joke_detail.py    # Detail panel
│       │   ├── filter_bar.py     # Filter controls
│       │   └── stats_header.py   # Progress/stats header
│       ├── screens/
│       │   ├── review_screen.py  # Main review screen
│       │   ├── edit_modal.py     # NEW: Edit joke modal
│       │   └── help_screen.py    # Keyboard shortcuts help
│       └── actions.py            # Review actions (approve/reject/etc)
tests/
└── test_importers/
    └── test_tui.py               # TUI component tests
```

## Key Features

### 1. Keyboard Navigation
- **j/k** or **↓/↑** - Navigate up/down
- **g/G** - Jump to top/bottom
- **Page Up/Down** - Page navigation
- **Enter** - Expand/collapse detail view
- **Tab** - Cycle through filters

### 2. Quick Actions
- **a** - Approve selected joke
- **r** - Reject (prompts for reason)
- **f** - Flag for manual review
- **s** - Skip to next
- **u** - Undo last action
- **e** - Edit joke content and metadata
- **Space** - Toggle selection (for bulk actions)
- **Shift+A** - Approve all selected
- **Shift+R** - Reject all selected

### 3. Filtering & Sorting
- **/** - Open filter dialog
- Filter by: maturity, score range, flags, categories, status
- Sort by: score, date, ID, length
- Save filter presets

### 4. Detail Panel
- Expandable detail view for selected joke
- Full content display (setup, punchline, continuation)
- All metadata (categories, mechanisms, tags)
- Source information and ratings
- Similar duplicates (if any)

### 5. Progress Tracking
- Real-time stats header
- Session statistics (approved/rejected/flagged counts)
- Overall progress bar
- Estimated time remaining

### 6. Undo/History
- Undo last N actions (configurable, default 50)
- Review action history
- Bulk undo by filter

### 7. Batch Operations
- Select multiple jokes with Space
- Bulk approve/reject/flag
- Clear selection

### 8. Search
- **Ctrl+F** - Search joke content
- **n/N** - Next/previous match
- Highlight matches in table

### 9. Inline Editing
- **e** - Open edit modal for selected joke
- Edit joke content (setup, punchline, continuation)
- Modify metadata (maturity rating, categories, mechanisms, tags)
- Add/remove flags (NSFW, explicit, political, etc.)
- Update ratings if needed
- Changes saved immediately to staging database
- Edit history tracked for audit trail

## User Workflow

### Launch Review Session

```bash
# Start interactive review for import batch
uv run python -m joke_emporium.importers.cli review-interactive <import_id>

# Start with filters pre-applied
uv run python -m joke_emporium.importers.cli review-interactive <import_id> \
  --maturity R \
  --min-score 30 \
  --max-score 70

# Review only flagged jokes
uv run python -m joke_emporium.importers.cli review-interactive <import_id> \
  --status UNDER_REVIEW
```

### Review Session Flow

1. **TUI launches** - Shows pending jokes in table
2. **Navigate** - Use j/k to move through jokes
3. **Review** - Press Enter to expand detail view
4. **Decide** - Press a/r/f/s for action
5. **Continue** - Auto-advances to next joke
6. **Filter** - Press / to refine list
7. **Quit** - Press q, confirms before exit

### Example Session

```
Reviewer opens TUI with 1,250 pending jokes
→ Filters to maturity=R, score 30-70 (500 jokes remain)
→ Reviews first joke (borderline NSFW humor)
→ Presses 'e' to edit - changes maturity from R to PG-13, adds "INNUENDO" tag
→ Presses 'a' to approve
→ Auto-advances to next joke
→ Presses 'r' to reject, types reason "Too explicit"
→ Continues reviewing...
→ Finds a joke with typo in punchline
→ Presses 'e' to edit, fixes typo, saves
→ Presses 'a' to approve the corrected joke
→ After 50 jokes, presses 'u' to undo last rejection
→ Changes to approve instead
→ After 200 jokes, presses 'q' to quit
→ TUI shows summary: 180 approved, 15 rejected, 5 flagged, 3 edited
→ Asks for confirmation to save changes
```

## Implementation Steps

### Phase 1: Basic TUI (Days 1-2)
1. Set up Textual app structure
2. Create joke table widget with pagination
3. Implement keyboard navigation (j/k)
4. Add approve/reject/skip actions
5. Basic stats header

### Phase 2: Detail View (Days 3-4)
6. Expandable detail panel
7. Full joke content rendering
8. Metadata display
9. Source information

### Phase 3: Filtering (Days 5-6)
10. Filter bar widget
11. Filter dialog
12. Dynamic filtering
13. Sort controls

### Phase 4: Advanced Features (Days 7-8)
14. Undo functionality
15. Bulk selection and actions
16. Search functionality
17. Inline editing modal
18. Help screen
19. Session persistence (save/resume)

## Technical Details

### Textual App Structure

```python
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Footer, Static
from textual.containers import Container, Vertical, Horizontal

class ReviewApp(App):
    """Interactive joke review TUI."""

    CSS = """
    JokeTable {
        height: 60%;
    }
    DetailPanel {
        height: 40%;
        border: solid green;
    }
    """

    BINDINGS = [
        ("a", "approve", "Approve"),
        ("r", "reject", "Reject"),
        ("f", "flag", "Flag"),
        ("e", "edit", "Edit"),
        ("s", "skip", "Skip"),
        ("u", "undo", "Undo"),
        ("q", "quit", "Quit"),
        ("/", "filter", "Filter"),
    ]

    def __init__(self, import_batch_id: str, session):
        super().__init__()
        self.import_batch_id = import_batch_id
        self.session = session
        self.jokes = []
        self.current_index = 0
        self.history = []  # For undo

    def compose(self) -> ComposeResult:
        yield Header()
        yield StatsHeader()  # Progress and session stats
        yield FilterBar()    # Filter controls
        yield JokeTable()    # Main joke table
        yield DetailPanel()  # Expandable detail view
        yield Footer()       # Keyboard shortcuts

    def on_mount(self) -> None:
        self.load_jokes()
        self.update_table()

    def action_approve(self) -> None:
        joke = self.get_current_joke()
        self.mark_approved(joke)
        self.history.append(("approve", joke.id))
        self.advance_to_next()

    def action_edit(self) -> None:
        joke = self.get_current_joke()
        self.push_screen(EditJokeModal(joke), callback=self.handle_edit_complete)

    def handle_edit_complete(self, edited_joke: StagingJokeDB | None) -> None:
        if edited_joke:
            self.save_joke_changes(edited_joke)
            self.history.append(("edit", edited_joke.id, self.get_joke_snapshot(edited_joke)))
            self.refresh_current_row()

    # ... other actions
```

### Joke Table Widget

```python
class JokeTable(DataTable):
    """Paginated table of jokes for review."""

    def on_mount(self) -> None:
        self.add_columns("ID", "Preview", "Score", "Maturity", "Flags", "Status")
        self.cursor_type = "row"
        self.zebra_stripes = True

    def populate(self, jokes: list[StagingJokeDB]) -> None:
        self.clear()
        for joke in jokes:
            self.add_row(
                joke.staging_id[:8],
                self.truncate(joke.text_preview, 40),
                f"{joke.weighted_avg_funniness:.1f}" if joke.weighted_avg_funniness else "-",
                joke.maturity_rating.value,
                self.format_flags(joke.flags),
                joke.review_status.value
            )
```

### Filter System

```python
@dataclass
class ReviewFilter:
    """Filter criteria for review session."""
    maturity_ratings: list[MaturityRating] | None = None
    min_score: float | None = None
    max_score: float | None = None
    has_flags: list[str] | None = None
    no_flags: list[str] | None = None
    status: ReviewStatus | None = None
    search_text: str | None = None

    def matches(self, joke: StagingJokeDB) -> bool:
        """Check if joke matches filter criteria."""
        if self.maturity_ratings and joke.maturity_rating not in self.maturity_ratings:
            return False
        if self.min_score and joke.weighted_avg_funniness < self.min_score:
            return False
        # ... other filters
        return True
```

## Edge Cases & Considerations

1. **Large datasets** - Paginate/lazy-load for 50k+ jokes
2. **Terminal size** - Responsive layout, minimum 80x24
3. **Session persistence** - Save state, resume later
4. **Network/DB errors** - Graceful error handling, retry logic
5. **Concurrent edits** - Warn if batch modified externally
6. **Unicode rendering** - Ensure emojis/special chars display correctly
7. **Performance** - Smooth scrolling even with 1000s of jokes

## Testing Strategy

### Unit Tests
- Filter matching logic
- Action handlers (approve/reject/undo)
- Pagination calculations
- Keyboard binding handlers

### Integration Tests
- TUI app lifecycle
- Database interaction (approve commits changes)
- Filter application to real jokes
- Undo history

### Manual Testing
- Test on various terminal emulators (Windows Terminal, iTerm2, etc.)
- Test with different terminal sizes
- Test with real import batch
- Test all keyboard shortcuts
- Test with colorblind-friendly theme

## Performance Requirements

- Launch time: < 2 seconds for 50k jokes
- Navigation: < 100ms response to keypress
- Filter application: < 500ms for 50k jokes
- Memory usage: < 500MB for 50k jokes

## Accessibility

- Keyboard-only navigation (no mouse required)
- High contrast mode option
- Screen reader compatible (future)
- Colorblind-friendly color scheme

## Configuration

```yaml
# config/tui_settings.yaml
tui:
  page_size: 20
  undo_history_size: 50
  auto_advance: true
  confirm_on_quit: true
  theme: "dark"  # or "light", "high_contrast"

  keybindings:
    approve: "a"
    reject: "r"
    flag: "f"
    skip: "s"
    undo: "u"
    # ... customizable
```

## Future Enhancements (Out of Scope)

- Mouse support (click to select)
- Multi-pane view (compare jokes side-by-side)
- Export filtered results to CSV
- Collaborative review (multiple reviewers)
- Review analytics dashboard
- Plugin system for custom actions
- Web-based version (same UX, browser interface)

## Dependencies

- `textual` - TUI framework (~500kb)
- `rich` - Already in project (text formatting)
- No other new dependencies

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Textual learning curve | Use examples, start simple, iterate |
| Terminal compatibility | Test on Windows/Mac/Linux terminals |
| Performance with large datasets | Implement pagination, lazy loading |
| Accidental bulk approvals | Confirm before bulk actions, undo support |
| Complex filter UI | Start with simple filters, add gradually |

## Success Criteria

1. Can review 100 jokes in < 10 minutes
2. All keyboard shortcuts work reliably
3. Filters apply instantly (< 500ms)
4. No crashes or data loss during session
5. Undo works for last 50 actions
6. Works on Windows Terminal, iTerm2, and common Linux terminals
7. User prefers TUI over CLI for manual review

## Related Documents

- [docs/HANDOFF_POLICY_ENGINE.md](HANDOFF_POLICY_ENGINE.md) - Auto-approval system
- [docs/DATABASE.md](DATABASE.md) - Staging database schema
- [docs/IMPORT_PLAN.md](IMPORT_PLAN.md) - Import framework overview
- Textual docs: https://textual.textualize.io/
- Industry reference: k9s (Kubernetes TUI), lazygit, tig

# TUI Improvements and Import Design

**Status:** Planning
**Priority:** P1 (Short-term)
**Effort:** 2-3 weeks total
**Impact:** Transform manual review and import workflows from tedious to efficient
**Date:** 2025-12-17

## Table of Contents

1. [Review TUI Improvements](#1-review-tui-improvements)
2. [Future Enhancements for Review TUI](#2-future-enhancements-for-review-tui)
3. [NEW: Import TUI Design](#3-new-import-tui-design)
4. [Integration Between Import and Review TUIs](#4-integration-between-import-and-review-tuis)
5. [Implementation Roadmap](#5-implementation-roadmap)

---

## 1. Review TUI Improvements

Based on analysis of `docs/HANDOFF_INTERACTIVE_REVIEW.md`, here are recommended enhancements to the existing review TUI design.

### 1.1 UX Improvements for Better Workflows

#### 1.1.1 Smart Navigation and Context Switching

**Problem:** Current design shows one joke at a time with limited context.

**Enhancement: Split-Pane View with Context**
```
┌─ Review Session: abc-123 ──────────────────────────────────────────────────┐
│ Progress: 234/1,250 (18.7%) │ Session: 45 approved, 12 rejected, 3 flagged │
├───────────────────────────────────────┬────────────────────────────────────┤
│ JOKE LIST (Press TAB to switch)      │ DETAIL VIEW (Current: stg_001)     │
├───────────────────────────────────────┤                                    │
│ ID     │ Preview         │Score│Mat │ Setup: Why did the chicken cross   │
├────────┼─────────────────┼─────┼────┤ the road?                          │
│►stg_001│Why did the ch...│ 85.3│  G ││                                    │
│ stg_002│A priest, a ra...│ 42.1│  R ││ Punchline: To get to the other    │
│ stg_003│What's the dif...│ 91.2│  G ││ side!                             │
│ stg_004│Yo mama so fat...│ 15.8│  R ││                                    │
│ stg_005│Knock knock...   │ 73.4│ PG ││ Categories: ANIMALS, WORDPLAY     │
├───────────────────────────────────────┤ Structure: QUESTION_ANSWER        │
│ Quick Actions:                        │ Mechanisms: INCONGRUITY           │
│ [A]pprove [R]eject [F]lag [E]dit     │                                    │
│ [Space]Select [Enter]Expand          │ Source: reddit.com/r/jokes        │
│                                       │ (u/comedian123, 2023-05-15)       │
│ [1-5]Rate  [C]ategory  [M]aturity    │                                    │
│ [/]Filter [S]ort [?]Help [Q]uit      │ Ratings: Funniness 85.3/100       │
└───────────────────────────────────────┴────────────────────────────────────┘
```

**Benefits:**
- See multiple jokes in context (helps identify patterns)
- Faster navigation without losing place
- Compare similar jokes side-by-side
- TAB switches focus between list and detail panes

#### 1.1.2 Quick Rating System

**Enhancement: Numeric Keyboard Shortcuts for Fast Rating**
```python
# New keyboard shortcuts in review flow
BINDINGS = [
    ("1", "rate_1", "Rate 1 star"),
    ("2", "rate_2", "Rate 2 stars"),
    ("3", "rate_3", "Rate 3 stars"),
    ("4", "rate_4", "Rate 4 stars"),
    ("5", "rate_5", "Rate 5 stars"),
    ("a", "approve_with_rating", "Auto-approve if rating >= 4"),
]

def action_rate(self, rating: int) -> None:
    """Quick rate current joke without opening modal."""
    joke = self.get_current_joke()

    # Add personal rating
    self.add_reviewer_rating(joke, rating)

    # Auto-approve if high rating
    if rating >= 4:
        self.mark_approved(joke)
        self.advance_to_next()
    else:
        # Just save rating, stay on joke
        self.save_current()
```

**Benefits:**
- Speed up review by 50% for clear-cut decisions
- Reduce cognitive load (press 4 or 5 instead of A then confirm)
- Build reviewer confidence scores for analytics

#### 1.1.3 Bulk Operations with Visual Feedback

**Enhancement: Multi-Select with Preview**
```
┌─ Bulk Action: 12 jokes selected ──────────────────────────────────────────┐
│                                                                             │
│ Action: [Approve All] [Reject All] [Change Maturity] [Add Tag]            │
│                                                                             │
│ Preview of affected jokes:                                                 │
│ ☑ stg_001  Why did the chicken...                        G    85.3        │
│ ☑ stg_003  What's the difference...                      G    91.2        │
│ ☑ stg_007  How many programmers...                       PG   78.9        │
│ ☑ stg_012  A photon checks into...                       G    82.1        │
│ ☑ ... 8 more                                                               │
│                                                                             │
│ ⚠ WARNING: This will approve 12 jokes. Continue?                           │
│ [ Yes (Ctrl+Enter) ] [ No (Esc) ]                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Clear preview prevents accidents
- Confirm dialog shows exact impact
- Undo remains available after bulk action
- Progress bar during bulk operation

#### 1.1.4 Smart Filters with Saved Presets

**Enhancement: Filter Presets and Quick Toggles**
```
┌─ Filters ───────────────────────────────────────────────────────────────┐
│                                                                          │
│ Presets: [Needs Review] [High Quality] [Borderline R-rated] [My Custom]│
│                                                                          │
│ Quick Toggles (click to toggle):                                        │
│ ☐ NSFW only     ☑ Pending only    ☐ No categories    ☐ Low scores     │
│                                                                          │
│ Advanced Filters:                                                        │
│ Maturity: [All ▼] [G] [PG] [PG-13] [R] [X]                            │
│ Score Range: [0] ━━━━━━●━━━━━━ [100]  (Current: 30-100)               │
│ Status: [Pending ▼]                                                     │
│ Categories: [Any ▼] Contains: [_____________]                           │
│ Flags: [Any with NSFW ▼] [_____________]                               │
│ Text Search: [___________________________________]                       │
│                                                                          │
│ [ Apply Filter ] [ Save as Preset ] [ Reset ] [ Cancel ]               │
└──────────────────────────────────────────────────────────────────────────┘
```

**Save Preset Implementation:**
```python
# config/tui_filter_presets.yaml
presets:
  needs_review:
    name: "Needs Review"
    filters:
      status: UNDER_REVIEW
      sort: added_date_desc

  high_quality:
    name: "High Quality"
    filters:
      min_score: 80
      status: PENDING
      sort: score_desc

  borderline_r_rated:
    name: "Borderline R-rated"
    filters:
      maturity: ["PG-13", "R"]
      min_score: 40
      max_score: 70
      sort: score_asc  # Review lowest first
```

**Benefits:**
- One-click access to common filter combinations
- Share presets across team
- Customize workflows per reviewer preference
- Reduce time spent reconfiguring filters

### 1.2 Additional Features for Efficiency

#### 1.2.1 Keyboard Maestro: Combo Actions

**Enhancement: Multi-Key Sequences for Complex Actions**
```python
# Press 'a' then 't' to approve and add tag in one flow
COMBO_BINDINGS = [
    ("a,t", "approve_and_tag", "Approve + Add Tag"),
    ("a,c", "approve_and_categorize", "Approve + Edit Categories"),
    ("r,d", "reject_as_duplicate", "Reject as Duplicate"),
    ("r,l", "reject_as_low_quality", "Reject (Low Quality)"),
    ("e,m", "edit_maturity", "Quick Edit Maturity"),
    ("e,c", "edit_categories", "Quick Edit Categories"),
]

def action_approve_and_tag(self) -> None:
    """Approve joke and open quick tag dialog."""
    self.mark_approved(self.get_current_joke())
    self.push_screen(QuickTagModal(self.get_current_joke()), self.save_and_advance)
```

**Visual Feedback:**
```
┌─ Combo Action Mode ─────────────────────────────────────────────────────┐
│ Pressed: 'a' (Approve)                                                   │
│                                                                          │
│ Next Action:                                                             │
│   t - Add Tag         c - Edit Categories     [Enter] - Confirm         │
│   [Esc] - Cancel                                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Power users can chain actions without modal dialogs
- Learn sequences over time (like Vim)
- Visual hints guide learning curve
- Fallback to simple actions always available

#### 1.2.2 Policy Engine Integration

**Enhancement: Show Policy Recommendations in UI**
```
┌─ Policy Assistant ──────────────────────────────────────────────────────┐
│ 🤖 Policy Engine Recommendation:                                         │
│                                                                          │
│ ✓ Auto-Approve Suggested (Confidence: 94%)                              │
│                                                                          │
│ Reasons:                                                                 │
│ • High quality score (85.3) > threshold (80)                            │
│ • G-rated with no flags                                                 │
│ • Common categories (ANIMALS, WORDPLAY)                                 │
│ • No profanity detected                                                 │
│                                                                          │
│ Override: [A]ccept recommendation [R]eject [M]anual review              │
└──────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Reduce reviewer decision fatigue
- Learn from policy engine suggestions
- Override when needed (human in the loop)
- Train policy engine with reviewer feedback

#### 1.2.3 Duplicate Detection Visualization

**Enhancement: Show Similar Jokes During Review**
```
┌─ Potential Duplicates Found (3) ───────────────────────────────────────┐
│                                                                          │
│ Current Joke (stg_001):                                                  │
│ "Why did the chicken cross the road? To get to the other side!"         │
│                                                                          │
│ Similar Jokes:                                                           │
│ 1. [95% match] prod_12345 (Already in production)                       │
│    "Why did the chicken cross the road? To get to the other side."      │
│    Action: [Mark as Duplicate] [Keep Both]                              │
│                                                                          │
│ 2. [87% match] stg_045 (In staging)                                     │
│    "Why'd the chicken cross the road? To get to the other side!"        │
│    Action: [Mark Both as Duplicates] [Keep Better One]                  │
│                                                                          │
│ 3. [72% match] prod_67890 (Already in production)                       │
│    "What did the chicken cross the road for? The other side."           │
│    Action: [Not a Duplicate] [Maybe Similar]                            │
│                                                                          │
│ [ Bulk Action: Reject Current as Duplicate ] [ Ignore All ] [ Close ]  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Catch duplicates during manual review
- Choose best version when duplicates found
- Avoid polluting production database
- Visual diff helps with edge cases

### 1.3 Performance Optimizations

#### 1.3.1 Lazy Loading and Pagination

**Current Issue:** Loading 50k jokes into memory upfront.

**Enhancement: Virtual Scrolling with Database Queries**
```python
class JokeTable(DataTable):
    """Paginated table with lazy loading."""

    PAGE_SIZE = 50  # Load 50 jokes at a time
    PREFETCH_PAGES = 2  # Prefetch next 2 pages

    def __init__(self):
        super().__init__()
        self.current_page = 0
        self.total_jokes = 0
        self.loaded_jokes = {}  # Cache: page_num -> list[jokes]
        self.prefetch_queue = asyncio.Queue()

    def on_mount(self) -> None:
        """Load first page and prefetch next pages."""
        self.load_page(0)
        self.start_prefetch_worker()

    def load_page(self, page_num: int) -> None:
        """Load jokes for specific page from database."""
        if page_num in self.loaded_jokes:
            return  # Already loaded

        offset = page_num * self.PAGE_SIZE
        jokes = self.db_query(
            status=self.current_filter.status,
            limit=self.PAGE_SIZE,
            offset=offset
        )
        self.loaded_jokes[page_num] = jokes

        # Trigger prefetch
        for i in range(1, self.PREFETCH_PAGES + 1):
            self.prefetch_queue.put_nowait(page_num + i)

    def on_scroll(self, event: Scroll) -> None:
        """Detect when user approaches page boundary."""
        current_row = self.cursor_row
        current_page = current_row // self.PAGE_SIZE

        if current_page != self.current_page:
            self.load_page(current_page)
            self.current_page = current_page
```

**Benefits:**
- Launch time < 1 second for any dataset size
- Memory usage: ~10MB for 50k jokes (vs 500MB loading all)
- Smooth scrolling with prefetch
- Database remains source of truth

#### 1.3.2 Caching and Incremental Refresh

**Enhancement: Smart Cache Invalidation**
```python
class ReviewCache:
    """Cache review data with smart invalidation."""

    def __init__(self):
        self.joke_cache = {}  # joke_id -> joke_data
        self.stats_cache = None
        self.last_refresh = datetime.now(UTC)

    def get_joke(self, joke_id: int) -> StagingJokeDB:
        """Get joke from cache or database."""
        if joke_id not in self.joke_cache:
            self.joke_cache[joke_id] = self.db.get_joke(joke_id)
        return self.joke_cache[joke_id]

    def invalidate_joke(self, joke_id: int) -> None:
        """Invalidate cache for specific joke after edit."""
        self.joke_cache.pop(joke_id, None)
        self.stats_cache = None  # Stats might have changed

    def invalidate_stats(self) -> None:
        """Invalidate stats cache after approve/reject."""
        self.stats_cache = None

    def get_stats(self) -> dict:
        """Get session stats with caching."""
        if not self.stats_cache or self._needs_refresh():
            self.stats_cache = self.db.get_review_stats()
            self.last_refresh = datetime.now(UTC)
        return self.stats_cache

    def _needs_refresh(self) -> bool:
        """Check if cache needs refresh (every 10 seconds)."""
        return (datetime.now(UTC) - self.last_refresh).seconds > 10
```

**Benefits:**
- Reduce database queries by 80%
- Sub-100ms response to actions
- Smart invalidation keeps data fresh
- Background refresh for stats

### 1.4 Accessibility Improvements

#### 1.4.1 Screen Reader Support

**Enhancement: ARIA Labels and Screen Reader Modes**
```python
class AccessibleReviewApp(ReviewApp):
    """Review TUI with screen reader support."""

    SCREEN_READER_MODE = True  # Detect automatically or via --screen-reader flag

    def announce(self, message: str, priority: str = "polite") -> None:
        """Announce message to screen reader."""
        if self.SCREEN_READER_MODE:
            # Use system screen reader API
            self.screen_reader.announce(message, priority)

    def action_approve(self) -> None:
        """Approve with screen reader feedback."""
        joke = self.get_current_joke()
        self.mark_approved(joke)

        # Announce action
        self.announce(
            f"Approved joke {joke.staging_id}. "
            f"{self.stats.approved_count} total approved. "
            f"Moving to next joke.",
            priority="assertive"
        )

        self.advance_to_next()

    def on_joke_selected(self, joke: StagingJokeDB) -> None:
        """Announce joke details when selected."""
        if self.SCREEN_READER_MODE:
            text = self._get_joke_text(joke)
            self.announce(
                f"Joke {joke.staging_id}. "
                f"Status: {joke.review_status}. "
                f"Maturity: {joke.maturity_rating}. "
                f"Score: {joke.weighted_avg_funniness or 'not rated'}. "
                f"Text: {text}"
            )
```

**Benefits:**
- Accessible to blind/low-vision reviewers
- Complies with accessibility standards
- Audio feedback reduces eye strain
- Can review while listening

#### 1.4.2 Colorblind-Friendly Themes

**Enhancement: Multiple Theme Options**
```python
# config/tui_themes.yaml
themes:
  default:
    background: "#1e1e1e"
    foreground: "#d4d4d4"
    approved: "#4ec9b0"      # Teal
    rejected: "#f48771"      # Coral
    pending: "#dcdcaa"       # Yellow
    flagged: "#c586c0"       # Purple

  high_contrast:
    background: "#000000"
    foreground: "#ffffff"
    approved: "#00ff00"      # Bright green
    rejected: "#ff0000"      # Bright red
    pending: "#ffff00"       # Bright yellow
    flagged: "#ff00ff"       # Bright magenta

  colorblind_safe:
    # Based on Paul Tol's colorblind-safe palette
    background: "#1e1e1e"
    foreground: "#d4d4d4"
    approved: "#44AA99"      # Teal (safe for all types)
    rejected: "#EE7733"      # Orange (safe for all types)
    pending: "#CCBB44"       # Yellow (safe for all types)
    flagged: "#AA3377"       # Purple (safe for all types)

  light:
    background: "#ffffff"
    foreground: "#000000"
    approved: "#008000"
    rejected: "#c41e3a"
    pending: "#ff8c00"
    flagged: "#4b0082"
```

**CLI Option:**
```bash
# Use specific theme
uv run python -m joke_emporium.importers.cli review-interactive <import_id> --theme colorblind_safe

# High contrast mode for low vision
uv run python -m joke_emporium.importers.cli review-interactive <import_id> --theme high_contrast
```

**Benefits:**
- Accessible to ~8% of males with color vision deficiency
- High contrast mode for low vision
- Light theme for bright environments
- Customizable per reviewer preference

#### 1.4.3 Keyboard-Only Navigation Enhancements

**Enhancement: Vim-like Navigation and Focus Management**
```python
EXTENDED_BINDINGS = [
    # Vim-like navigation
    ("h", "focus_left", "Focus left pane"),
    ("l", "focus_right", "Focus right pane"),
    ("j", "move_down", "Move down"),
    ("k", "move_up", "Move up"),
    ("g,g", "jump_top", "Jump to top"),
    ("G", "jump_bottom", "Jump to bottom"),

    # Focus management
    ("tab", "cycle_focus", "Cycle focus forward"),
    ("shift+tab", "cycle_focus_back", "Cycle focus backward"),
    ("ctrl+1", "focus_table", "Focus joke table"),
    ("ctrl+2", "focus_detail", "Focus detail pane"),
    ("ctrl+3", "focus_filters", "Focus filter bar"),

    # Jump to sections
    ("ctrl+s", "jump_to_stats", "Jump to stats"),
    ("ctrl+f", "jump_to_filters", "Jump to filters"),
    ("ctrl+a", "jump_to_actions", "Jump to actions"),
]
```

**Visual Focus Indicators:**
```
┌─ [FOCUSED] Joke List ──────┬─ Detail View ──────────────┐
│ ID     │ Preview      │...  │                            │
├────────┼──────────────┼─────┤ Setup: Why did...          │
│►stg_001│Why did the...│ 85.3│                            │
│ stg_002│A priest,...  │ 42.1│                            │
└────────────────────────────┴────────────────────────────┘

# Focus moves to detail pane:
┌─ Joke List ────────────────┬─ [FOCUSED] Detail View ────┐
│ ID     │ Preview      │...  │                            │
├────────┼──────────────┼─────┤ ▶ Setup: Why did...        │
│►stg_001│Why did the...│ 85.3│                            │
│ stg_002│A priest,...  │ 42.1│   [Press Ctrl+C to copy]   │
└────────────────────────────┴────────────────────────────┘
```

**Benefits:**
- Pure keyboard navigation (no mouse needed)
- Familiar to Vim users
- Clear visual feedback on focus
- Efficient for power users

---

## 2. Future Enhancements for Review TUI

These features would be valuable long-term but can be deferred to later sprints.

### 2.1 Advanced Filtering and Search

#### 2.1.1 Regex and Full-Text Search

**Feature: Search with Boolean Operators**
```
┌─ Advanced Search ──────────────────────────────────────────────────────┐
│                                                                         │
│ Search Mode: [Regex ▼] [Simple] [Fuzzy] [Boolean]                     │
│                                                                         │
│ Query: (chicken OR rooster) AND (road OR street) NOT dead             │
│                                                                         │
│ Search In:                                                              │
│ ☑ Setup    ☑ Punchline    ☐ Tags    ☐ Categories                     │
│                                                                         │
│ Results: 47 jokes found                                                │
│                                                                         │
│ [ Search ] [ Save Query ] [ Load Query ] [ Clear ]                    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Use Cases:**
- Find all political jokes without religious content
- Search for specific joke structures (regex patterns)
- Fuzzy search for typos and variations
- Save complex queries for reuse

#### 2.1.2 Semantic Search with Embeddings

**Feature: "Find Similar" Based on Meaning**
```python
# Future: Use sentence transformers for semantic similarity
class SemanticSearch:
    """Search jokes by semantic meaning, not just keywords."""

    def __init__(self):
        # Load model once at startup
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings_cache = {}

    def find_similar(self, query_joke: str, top_k: int = 10) -> list[StagingJokeDB]:
        """Find jokes similar in meaning to query."""
        query_embedding = self.model.encode(query_joke)

        # Compute similarities
        similarities = []
        for joke in self.all_jokes:
            joke_embedding = self._get_embedding(joke)
            similarity = cosine_similarity(query_embedding, joke_embedding)
            similarities.append((joke, similarity))

        # Return top K
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [joke for joke, _ in similarities[:top_k]]
```

**Use Cases:**
- Find jokes with similar themes but different wording
- Discover potential duplicates with paraphrasing
- Group jokes by humor style
- Build recommendation system

### 2.2 Batch Operations Improvements

#### 2.2.1 Smart Batch Actions

**Feature: Conditional Batch Operations**
```
┌─ Smart Batch Action ───────────────────────────────────────────────────┐
│                                                                         │
│ Action: Approve all jokes matching:                                    │
│                                                                         │
│ ☑ Score >= 80                                                          │
│ ☑ Maturity = G or PG                                                   │
│ ☑ No NSFW flags                                                        │
│ ☐ Categories include: [______________]                                │
│ ☐ Has at least N ratings: [___]                                       │
│                                                                         │
│ Matching jokes: 234 of 1,250                                           │
│                                                                         │
│ ⚠ This will approve 234 jokes. Add review note?                       │
│ Note: [Auto-approved: high quality, family-friendly_____________]     │
│                                                                         │
│ [ Execute Batch Action ] [ Preview List ] [ Cancel ]                  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Approve/reject based on complex criteria
- Audit trail with batch notes
- Preview before executing
- Combine with policy engine rules

#### 2.2.2 Undo/Redo with Branching

**Feature: Advanced History with Branches**
```
┌─ Action History (50 actions) ──────────────────────────────────────────┐
│                                                                         │
│ Timeline:                                                               │
│ 10:34:21 - Approved stg_001 [current state]                           │
│ 10:34:15 - Rejected stg_002 (reason: low quality)                     │
│ 10:33:58 - Edited stg_003 (changed maturity R -> PG-13)               │
│ 10:33:45 - ├─ [BRANCH] Approved stg_004 (alternative decision)        │
│ 10:33:40 - └─ Rejected stg_004 (reason: duplicate)                    │
│ 10:33:30 - Batch approved 50 jokes (score >= 80)                      │
│                                                                         │
│ Actions:                                                                │
│ [ Undo Last ] [ Redo ] [ Jump to Checkpoint ] [ Create Branch ]       │
│                                                                         │
│ Checkpoints:                                                            │
│ • 10:30:00 - Session start (checkpoint 1)                              │
│ • 10:35:00 - After first 100 reviews (checkpoint 2)                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Undo complex multi-step actions
- Create checkpoints for experimentation
- Branch timeline for "what if" scenarios
- Detailed audit log for compliance

### 2.3 Analytics and Reporting

#### 2.3.1 Real-Time Review Analytics

**Feature: Dashboard View**
```
┌─ Review Analytics Dashboard ───────────────────────────────────────────┐
│                                                                         │
│ Session Performance:                                                    │
│ ┌─────────────────────────────────────────────────────────────────────┐│
│ │ Reviews per Hour: 156 jokes/hr  (Target: 120/hr)          ↑ +30%  ││
│ │ Avg Time per Joke: 23 seconds   (Baseline: 30s)           ↓ -23%  ││
│ │ Approval Rate: 68%               (Expected: 70%)           → +2%   ││
│ └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ Quality Metrics:                                                        │
│ ┌─────────────────────────────────────────────────────────────────────┐│
│ │ Avg Score of Approved: 82.3     (↑ from last session: 78.1)       ││
│ │ Rejection Reasons:                                                  ││
│ │   • Low quality: 45%    ███████████████                            ││
│ │   • Duplicate: 30%      ██████████                                 ││
│ │   • Inappropriate: 15%  █████                                      ││
│ │   • Other: 10%          ███                                        ││
│ └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ Reviewer Insights:                                                      │
│ • You approve G-rated jokes 85% of the time (avg: 70%)                │
│ • You reject NSFW jokes 95% of the time (avg: 80%)                    │
│ • Your ratings correlate 0.89 with community ratings                  │
│                                                                         │
│ [ Export Report ] [ Compare with Team ] [ Close ]                     │
└─────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Track reviewer productivity
- Identify bottlenecks
- Ensure quality standards
- Personalized feedback

#### 2.3.2 Export and Reporting

**Feature: Customizable Reports**
```bash
# Export review session to various formats
uv run python -m joke_emporium.importers.cli review-export <session_id> \
  --format csv \
  --fields id,status,score,maturity,tags \
  --output reports/session_2024_01_15.csv

# Generate HTML report with charts
uv run python -m joke_emporium.importers.cli review-export <session_id> \
  --format html \
  --include-analytics \
  --output reports/session_2024_01_15.html

# Export for external analysis (JSON)
uv run python -m joke_emporium.importers.cli review-export <session_id> \
  --format json \
  --include-raw-data \
  --output reports/session_2024_01_15.json
```

**Report Contents:**
- Review decisions with timestamps
- Score distributions
- Category breakdowns
- Reviewer performance metrics
- Charts and visualizations

### 2.4 Integration Possibilities

#### 2.4.1 Multi-Reviewer Collaboration

**Feature: Shared Review Sessions**
```
┌─ Collaborative Review Session ─────────────────────────────────────────┐
│                                                                         │
│ Reviewers Online (3):                                                  │
│ • alice (you) - Reviewing stg_001                                      │
│ • bob - Reviewing stg_045                                              │
│ • charlie - Idle (last action 2 min ago)                              │
│                                                                         │
│ Assignment Mode: [Round Robin ▼] [Random] [Manual] [Smart]           │
│                                                                         │
│ Consensus Mode:                                                         │
│ ☑ Require 2+ approvals for borderline jokes (score 40-60)            │
│ ☑ Flag disagreements for discussion                                   │
│ ☐ Auto-merge unanimous decisions                                      │
│                                                                         │
│ Chat:                                                                   │
│ ┌───────────────────────────────────────────────────────────────────┐ │
│ │ [bob]: stg_045 has duplicate in production (prod_123)             │ │
│ │ [you]: Thanks, marking as duplicate                                │ │
│ │ [charlie]: Taking a break, back in 15 min                         │ │
│ └───────────────────────────────────────────────────────────────────┘ │
│ Message: [_______________________________________] [Send (Enter)]     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Distribute review workload
- Improve quality with multiple eyes
- Reduce reviewer bias
- Enable remote collaboration

#### 2.4.2 Integration with Policy Engine

**Feature: Policy Learning from Manual Reviews**
```python
class PolicyLearner:
    """Learn from manual review decisions to improve policy engine."""

    def __init__(self):
        self.decisions = []

    def record_decision(
        self,
        joke: StagingJokeDB,
        reviewer_action: str,
        policy_suggestion: str,
        override_reason: str | None
    ) -> None:
        """Record reviewer decision for learning."""
        self.decisions.append({
            "joke_id": joke.id,
            "joke_features": self._extract_features(joke),
            "policy_suggested": policy_suggestion,
            "reviewer_decided": reviewer_action,
            "agreement": policy_suggestion == reviewer_action,
            "override_reason": override_reason,
            "timestamp": datetime.now(UTC),
        })

    def analyze_disagreements(self) -> dict:
        """Analyze cases where reviewer disagreed with policy."""
        disagreements = [d for d in self.decisions if not d["agreement"]]

        patterns = {
            "common_override_reasons": Counter(d["override_reason"] for d in disagreements),
            "feature_correlations": self._find_feature_patterns(disagreements),
            "suggested_rule_changes": self._suggest_rules(disagreements),
        }

        return patterns

    def export_training_data(self, output_path: Path) -> None:
        """Export decisions as training data for ML model."""
        df = pd.DataFrame(self.decisions)
        df.to_csv(output_path, index=False)
```

**Benefits:**
- Continuous improvement of policy engine
- Reduce manual review over time
- Learn reviewer preferences
- Build training data for ML models

---

## 3. NEW: Import TUI Design

This section proposes a comprehensive TUI for the import workflow, matching the review TUI's look and feel.

### 3.1 Overview

The import TUI transforms the current CLI-based import process into an interactive, user-friendly experience. Key features:

1. **Importer Discovery** - Automatically detect and list available importers
2. **Download-Only Mode** - Download data for inspection without importing
3. **Interactive Wizard** - Step-by-step import with progress tracking
4. **Configuration Management** - Save and reuse import configurations
5. **Live Progress** - Real-time stats during import
6. **Post-Import Summary** - Detailed results with next steps

### 3.2 Architecture

#### 3.2.1 File Structure

```
src/joke_emporium/
├── importers/
│   ├── tui/                        # NEW: Import TUI components
│   │   ├── __init__.py
│   │   ├── import_app.py           # Main import TUI app
│   │   ├── screens/
│   │   │   ├── discovery_screen.py # Importer selection screen
│   │   │   ├── config_screen.py    # Import configuration
│   │   │   ├── download_screen.py  # Download-only mode
│   │   │   ├── import_screen.py    # Live import progress
│   │   │   ├── summary_screen.py   # Post-import summary
│   │   │   └── help_screen.py      # Keyboard shortcuts help
│   │   ├── widgets/
│   │   │   ├── importer_list.py    # List of available importers
│   │   │   ├── progress_panel.py   # Live progress widget
│   │   │   ├── config_form.py      # Configuration form
│   │   │   └── stats_panel.py      # Statistics display
│   │   └── utils.py                # TUI utilities
│   ├── registry.py                 # NEW: Importer registry
│   └── cli.py                      # MODIFY: Add import-interactive command
```

#### 3.2.2 Importer Registry

To enable automatic discovery, create an importer registry:

```python
# src/joke_emporium/importers/registry.py
"""Registry for automatic importer discovery."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Type
import importlib
import pkgutil

from joke_emporium.importers.base import BaseImporter

@dataclass
class ImporterInfo:
    """Metadata about an importer."""
    name: str
    description: str
    source_url: str
    importer_class: Type[BaseImporter]
    estimated_count: int | None = None
    tags: list[str] = None
    requires_config: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class ImporterRegistry:
    """Central registry of all available importers."""

    _importers: dict[str, ImporterInfo] = {}

    @classmethod
    def register(
        cls,
        name: str,
        description: str,
        estimated_count: int | None = None,
        tags: list[str] | None = None,
        requires_config: bool = False,
    ):
        """Decorator to register an importer."""
        def decorator(importer_class: Type[BaseImporter]):
            cls._importers[name] = ImporterInfo(
                name=name,
                description=description,
                source_url=importer_class.source_url,
                importer_class=importer_class,
                estimated_count=estimated_count,
                tags=tags or [],
                requires_config=requires_config,
            )
            return importer_class
        return decorator

    @classmethod
    def get_importer(cls, name: str) -> ImporterInfo | None:
        """Get importer by name."""
        return cls._importers.get(name)

    @classmethod
    def list_importers(cls, tags: list[str] | None = None) -> list[ImporterInfo]:
        """List all registered importers, optionally filtered by tags."""
        importers = list(cls._importers.values())

        if tags:
            importers = [
                imp for imp in importers
                if any(tag in imp.tags for tag in tags)
            ]

        return sorted(importers, key=lambda x: x.name)

    @classmethod
    def auto_discover(cls) -> None:
        """Auto-discover all importers in the importers package."""
        # Import all modules in importers package
        import joke_emporium.importers
        package = joke_emporium.importers

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            if module_name.startswith('_') or module_name == 'base':
                continue
            try:
                importlib.import_module(f'joke_emporium.importers.{module_name}')
            except Exception as e:
                logger.warning(f"Failed to load importer module {module_name}: {e}")

# Usage in importers:
# src/joke_emporium/importers/taivop.py
@ImporterRegistry.register(
    name="taivop",
    description="Reddit jokes from taivop/joke-dataset (~208k jokes)",
    estimated_count=208_000,
    tags=["reddit", "large", "quality"],
    requires_config=False,
)
class TaivopImporter(BaseImporter):
    source_name = "taivop/joke-dataset"
    source_url = "https://github.com/taivop/joke-dataset"
    # ... rest of implementation
```

### 3.3 Screen-by-Screen Design

#### 3.3.1 Discovery Screen (Home)

This is the first screen users see when launching the import TUI.

```
┌─ Joke Emporium - Data Import Wizard ───────────────────────────────────┐
│                                                                         │
│ Select an importer to begin:                                           │
│                                                                         │
│ ┌─ Available Importers (3) ─────────────────────────────────────────┐ │
│ │                                                                     │ │
│ │ ► taivop                                [reddit] [large] [quality] │ │
│ │   Reddit jokes from taivop/joke-dataset                            │ │
│ │   Estimated: 208,000 jokes                                         │ │
│ │   Source: https://github.com/taivop/joke-dataset                  │ │
│ │   Status: ✓ Available | Last import: 2025-01-15 (234,567 jokes)  │ │
│ │                                                                     │ │
│ │   example_importer                              [example] [small] │ │
│ │   Example importer for reference implementation                    │ │
│ │   Estimated: ~100 jokes                                            │ │
│ │   Source: Internal fixtures                                        │ │
│ │   Status: ✓ Available | Never imported                            │ │
│ │                                                                     │ │
│ │   reddit_api (Coming Soon)                      [reddit] [api]    │ │
│ │   Direct import from Reddit API with live data                     │ │
│ │   Estimated: Unlimited                                             │ │
│ │   Status: ⚠ Not implemented                                        │ │
│ │                                                                     │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ Quick Actions:                                                          │
│ [Enter] Configure Import  [D] Download Only  [I] Import History       │
│ [F] Filter by Tags        [R] Refresh List   [?] Help  [Q] Quit       │
│                                                                         │
│ Filter: [All ▼] [reddit] [api] [scrapers] [large] [quality]          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Auto-discovers all registered importers
- Shows importer status (available, not implemented, failed)
- Displays last import stats (if any)
- Tag-based filtering
- Quick access to download-only mode
- Visual indicators for importer readiness

**Implementation:**
```python
# src/joke_emporium/importers/tui/screens/discovery_screen.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, ListItem
from textual.containers import Container, Vertical

from joke_emporium.importers.registry import ImporterRegistry

class DiscoveryScreen(Screen):
    """Importer discovery and selection screen."""

    BINDINGS = [
        ("enter", "select_importer", "Configure Import"),
        ("d", "download_only", "Download Only"),
        ("i", "import_history", "Import History"),
        ("f", "filter_tags", "Filter by Tags"),
        ("r", "refresh", "Refresh List"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Joke Emporium - Data Import Wizard", id="title")
        yield Static("Select an importer to begin:", id="subtitle")

        # Importer list
        yield ImporterListWidget(id="importer_list")

        # Quick actions bar
        yield Static(
            "[Enter] Configure Import  [D] Download Only  [I] Import History",
            id="quick_actions"
        )

        yield Footer()

    def on_mount(self) -> None:
        """Load importers on mount."""
        ImporterRegistry.auto_discover()
        self.refresh_importer_list()

    def refresh_importer_list(self) -> None:
        """Refresh the list of importers."""
        importers = ImporterRegistry.list_importers()
        importer_list = self.query_one("#importer_list", ImporterListWidget)
        importer_list.populate(importers)

    def action_select_importer(self) -> None:
        """Open configuration screen for selected importer."""
        importer_list = self.query_one("#importer_list", ImporterListWidget)
        selected = importer_list.get_selected()

        if selected:
            self.app.push_screen(ConfigScreen(selected))

    def action_download_only(self) -> None:
        """Open download-only mode for selected importer."""
        importer_list = self.query_one("#importer_list", ImporterListWidget)
        selected = importer_list.get_selected()

        if selected:
            self.app.push_screen(DownloadScreen(selected))
```

#### 3.3.2 Configuration Screen

Configure import parameters before starting.

```
┌─ Configure Import: taivop ──────────────────────────────────────────────┐
│                                                                         │
│ Import Options:                                                         │
│                                                                         │
│ ┌─ Basic Settings ────────────────────────────────────────────────────┐│
│ │                                                                      ││
│ │ Import Mode: [Full Import ▼] [Full] [Incremental] [Sample]        ││
│ │                                                                      ││
│ │ Max Records: [__________] (leave empty for all, ~208,000 jokes)    ││
│ │              [✓] Unlimited  [  ] Limit to: [____] records          ││
│ │                                                                      ││
│ │ Validation:  [✓] Validate jokes before import                       ││
│ │              [✓] Check for duplicates                               ││
│ │              [  ] Skip validation (faster, less safe)               ││
│ │                                                                      ││
│ │ Batch Size:  [100▼] jokes per commit                               ││
│ │              (smaller = slower but safer, larger = faster)          ││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ ┌─ Advanced Settings (Optional) ──────────────────────────────────────┐│
│ │                                                                      ││
│ │ Filters:                                                             ││
│ │   [  ] Import only specific categories: [_______________]           ││
│ │   [  ] Import only maturity levels: [All ▼]                        ││
│ │   [  ] Minimum score threshold: [__]                               ││
│ │                                                                      ││
│ │ Auto-Review:                                                         ││
│ │   [  ] Auto-approve jokes meeting quality threshold                 ││
│ │   [  ] Auto-reject jokes below quality threshold                    ││
│ │                                                                      ││
│ │ Staging Database: [default (data/staging.db)_____]                 ││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ Configuration Presets:                                                  │
│ [Quick Test (100 jokes)] [Full Import] [High Quality Only]            │
│ [Save Current Config] [Load Config...]                                │
│                                                                         │
│ Estimated Time: ~15 minutes for full import (208k jokes)               │
│ Disk Space Required: ~250 MB                                           │
│                                                                         │
│ [ Start Import (Enter) ] [ Download Only (D) ] [ Back (Esc) ]         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Presets for common configurations (quick test, full import)
- Save/load custom configurations
- Estimates time and disk space
- Advanced filters for selective imports
- Clear explanation of options

**Implementation:**
```python
# src/joke_emporium/importers/tui/screens/config_screen.py
from dataclasses import dataclass
from textual.screen import Screen
from textual.widgets import Input, Checkbox, Select, Button

@dataclass
class ImportConfig:
    """Import configuration."""
    importer_name: str
    max_records: int | None = None
    validate: bool = True
    check_duplicates: bool = True
    batch_size: int = 100
    staging_db: str | None = None

    # Filters
    categories: list[str] | None = None
    maturity_levels: list[str] | None = None
    min_score: float | None = None

    # Auto-review
    auto_approve_threshold: float | None = None
    auto_reject_threshold: float | None = None

class ConfigScreen(Screen):
    """Import configuration screen."""

    BINDINGS = [
        ("enter", "start_import", "Start Import"),
        ("d", "download_only", "Download Only"),
        ("escape", "back", "Back"),
    ]

    def __init__(self, importer_info: ImporterInfo):
        super().__init__()
        self.importer_info = importer_info
        self.config = ImportConfig(importer_name=importer_info.name)

    def action_start_import(self) -> None:
        """Start import with current configuration."""
        self._save_config_from_form()
        self.app.push_screen(ImportScreen(self.importer_info, self.config))

    def action_download_only(self) -> None:
        """Switch to download-only mode."""
        self._save_config_from_form()
        self.app.push_screen(DownloadScreen(self.importer_info))
```

#### 3.3.3 Download-Only Screen

Download data without importing to staging.

```
┌─ Download Data: taivop ─────────────────────────────────────────────────┐
│                                                                         │
│ Download source data for inspection without importing to database.     │
│                                                                         │
│ ┌─ Download Progress ─────────────────────────────────────────────────┐│
│ │                                                                      ││
│ │ Status: Downloading...                                              ││
│ │                                                                      ││
│ │ File: reddit_jokes.json                                             ││
│ │ Size: 47.3 MB / 52.1 MB (90.8%)                                     ││
│ │ ████████████████████░░░░░░░░░░░                                     ││
│ │                                                                      ││
│ │ Speed: 2.1 MB/s                                                     ││
│ │ ETA: 3 seconds                                                      ││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ Download Location: temp/imports/taivop/                                 │
│                                                                         │
│ Next Steps (after download):                                           │
│ • Inspect data files in temp/imports/taivop/                          │
│ • Run test imports with --max-records flag                            │
│ • Validate data format and quality                                    │
│ • Return here to start full import                                    │
│                                                                         │
│ [ Cancel (Esc) ]                                                       │
│                                                                         │
│ ─────────────────────── Download Complete ──────────────────────────── │
│                                                                         │
│ ✓ Downloaded: reddit_jokes.json (52.1 MB)                             │
│ ✓ Downloaded: stupidstuff.json (1.2 MB)                               │
│ ✓ Downloaded: wocka.json (3.4 MB)                                     │
│                                                                         │
│ Total Size: 56.7 MB                                                    │
│ Location: temp/imports/taivop/                                         │
│                                                                         │
│ [ Open Folder (O) ] [ Import Now (I) ] [ Back (Esc) ]                 │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Real-time download progress
- Multiple file support with individual progress
- Clear next steps after download
- Quick transition to import mode
- Open folder option for inspection

**Use Cases:**
- Test new importers before full import
- Inspect data format and quality
- Download for offline analysis
- Verify file integrity before import

#### 3.3.4 Import Progress Screen

Live progress during import with real-time stats.

```
┌─ Importing: taivop ─────────────────────────────────────────────────────┐
│                                                                         │
│ Import ID: abc-123-def-456                      Elapsed: 00:12:34      │
│                                                                         │
│ ┌─ Overall Progress ──────────────────────────────────────────────────┐│
│ │ 124,567 / 208,000 jokes processed (59.9%)                           ││
│ │ ████████████████████████████░░░░░░░░░░░░░░░░░░                     ││
│ │                                                                      ││
│ │ ETA: 00:08:12 remaining    Speed: 165 jokes/sec                     ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ ┌─ Current Phase: Transform ──────────────────────────────────────────┐│
│ │ 1. ✓ Download       (52.1 MB in 24s)                                ││
│ │ 2. ✓ Parse          (208,000 jokes found)                           ││
│ │ 3. ▶ Transform      (124,567 / 208,000) - 59.9%                    ││
│ │ 4. ⋯ Validate       (pending)                                       ││
│ │ 5. ⋯ Save to DB     (pending)                                       ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ ┌─ Live Statistics ───────────────────────────────────────────────────┐│
│ │ Successful:  119,234 (95.7%)   ████████████████████▓░              ││
│ │ Failed:        5,333 (4.3%)    ▓░░░░░░░░░░░░░░░░░░░░░              ││
│ │                                                                      ││
│ │ Recent Errors (last 10):                                            ││
│ │ • ValidationError: Missing punchline (5 occurrences)                ││
│ │ • TransformError: Invalid date format (3 occurrences)               ││
│ │ • KeyError: 'body' field not found (2 occurrences)                  ││
│ │                                                                      ││
│ │ [ View All Errors (E) ]                                             ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ ┌─ System Resources ──────────────────────────────────────────────────┐│
│ │ CPU: 45%  ██████████░░░░░░░░                                        ││
│ │ Memory: 234 MB / 512 MB (45.7%)  ██████████░░░░░░░░                ││
│ │ Disk I/O: 12.3 MB/s (write)                                         ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ [ Pause (P) ] [ View Logs (L) ] [ Cancel (Esc) ]                      │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Real-time progress with ETA
- Phase-by-phase breakdown
- Live statistics with error summary
- Resource monitoring (CPU, memory, disk I/O)
- Pause/resume capability
- Error drill-down

**Implementation:**
```python
# src/joke_emporium/importers/tui/screens/import_screen.py
from textual.screen import Screen
from textual.widgets import ProgressBar, Static
from textual.reactive import reactive

class ImportScreen(Screen):
    """Live import progress screen."""

    BINDINGS = [
        ("p", "pause", "Pause"),
        ("l", "view_logs", "View Logs"),
        ("e", "view_errors", "View Errors"),
        ("escape", "cancel", "Cancel"),
    ]

    # Reactive properties for live updates
    progress = reactive(0.0)
    processed = reactive(0)
    successful = reactive(0)
    failed = reactive(0)
    phase = reactive("Initializing")

    def __init__(self, importer_info: ImporterInfo, config: ImportConfig):
        super().__init__()
        self.importer_info = importer_info
        self.config = config
        self.import_task = None

    def on_mount(self) -> None:
        """Start import on mount."""
        self.start_import()

    async def start_import(self) -> None:
        """Start the import process."""
        from joke_emporium.importers.registry import ImporterRegistry
        from joke_emporium.db.staging import get_staging_session, init_staging_db

        # Initialize database
        init_staging_db()

        # Create importer instance
        importer_class = self.importer_info.importer_class
        importer = importer_class()

        # Start import in background task
        self.import_task = asyncio.create_task(self._run_import(importer))

    async def _run_import(self, importer: BaseImporter) -> None:
        """Run import with progress updates."""
        try:
            # Download phase
            self.phase = "Download"
            data_path = importer.download()

            # Parse phase
            self.phase = "Parse"
            # Count total for progress tracking
            if hasattr(importer, 'count_total_jokes'):
                total = importer.count_total_jokes(data_path)

            # Transform and validate phase
            self.phase = "Transform"

            with next(get_staging_session()) as session:
                # Use custom callback for progress updates
                metadata = importer.import_to_staging(
                    session=session,
                    validate=self.config.validate,
                    max_records=self.config.max_records,
                    progress_callback=self.update_progress,
                )

            # Complete
            self.app.push_screen(SummaryScreen(metadata))

        except Exception as e:
            self.app.push_screen(ErrorScreen(str(e)))

    def update_progress(self, stats: dict) -> None:
        """Update progress from importer callback."""
        self.processed = stats["processed"]
        self.successful = stats["successful"]
        self.failed = stats["failed"]
        self.progress = stats["processed"] / stats["total"] if stats["total"] > 0 else 0
```

#### 3.3.5 Summary Screen

Post-import summary with results and next steps.

```
┌─ Import Complete: taivop ───────────────────────────────────────────────┐
│                                                                         │
│ ✓ Import finished successfully!                                        │
│                                                                         │
│ Import ID: abc-123-def-456                                             │
│ Duration: 00:21:48                                                     │
│                                                                         │
│ ┌─ Results ────────────────────────────────────────────────────────────┐│
│ │                                                                      ││
│ │ Total Records:     208,000                                          ││
│ │ ✓ Successful:      199,234 (95.8%)   ████████████████████▓░        ││
│ │ ✗ Failed:            8,766 (4.2%)    ▓░░░░░░░░░░░░░░░░░░░░░        ││
│ │                                                                      ││
│ │ Import Rate:       159 jokes/sec                                    ││
│ │ Validation:        Enabled (100% checked)                           ││
│ │ Duplicates Found:  1,234 (marked for review)                        ││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ ┌─ Breakdown by Status ────────────────────────────────────────────────┐│
│ │ Pending (awaiting review):  199,234  (95.8%)                        ││
│ │ Auto-approved (high quality):    0   (0.0%)                         ││
│ │ Flagged (potential issues):  1,234  (0.6%)                          ││
│ │ Rejected (duplicates):       7,532  (3.6%)                          ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ ┌─ Error Summary ──────────────────────────────────────────────────────┐│
│ │ ValidationError: Missing punchline         5,234 (59.7%)            ││
│ │ TransformError: Invalid date format        2,103 (24.0%)            ││
│ │ KeyError: Missing 'body' field             1,429 (16.3%)            ││
│ │                                                                      ││
│ │ [ Export Error Log (CSV) ]                                          ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ Next Steps:                                                             │
│ 1. Review imported jokes:                                              │
│    uv run python -m joke_emporium.importers.cli review-interactive \   │
│      abc-123-def-456                                                   │
│                                                                         │
│ 2. Or use policy engine for auto-review (recommended):                │
│    uv run python -m joke_emporium.importers.cli auto-review \          │
│      abc-123-def-456 --min-score 80                                   │
│                                                                         │
│ 3. After review, merge to production:                                  │
│    uv run python -m joke_emporium.importers.cli merge abc-123-def-456 │
│                                                                         │
│ [ Start Review TUI (R) ] [ View Import History (H) ] [ Done (Enter) ] │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Comprehensive statistics
- Error breakdown with export option
- Clear next steps with copy-paste commands
- Quick transition to review TUI
- Save import report option

**Integration with Review TUI:**
```python
def action_start_review(self) -> None:
    """Launch review TUI for this import."""
    # Close import app and launch review app
    from joke_emporium.importers.tui.app import ReviewApp

    self.app.exit()

    # Launch review TUI with this import ID
    review_app = ReviewApp(import_batch_id=self.import_id)
    review_app.run()
```

### 3.4 Additional Import TUI Features

#### 3.4.1 Import History Browser

View past imports with detailed stats.

```
┌─ Import History ────────────────────────────────────────────────────────┐
│                                                                         │
│ Filter: [Last 30 days ▼] [All] [Successful] [Failed] [Partial]        │
│                                                                         │
│ ┌─ Recent Imports ─────────────────────────────────────────────────────┐│
│ │                                                                      ││
│ │ ► 2025-01-15 14:32  taivop         199,234 jokes  ✓ 95.8%          ││
│ │   abc-123-def-456   Duration: 21m 48s                               ││
│ │   Status: ✓ Complete | 1,234 pending review                         ││
│ │                                                                      ││
│ │   2025-01-14 09:15  taivop          50,000 jokes  ✓ 98.2%          ││
│ │   xyz-789-ghi-012   Duration: 5m 23s                                ││
│ │   Status: ✓ Merged to production (49,100 jokes)                     ││
│ │                                                                      ││
│ │   2025-01-13 16:45  example           100 jokes  ✓ 100%            ││
│ │   test-import-001   Duration: 12s                                   ││
│ │   Status: ⚠ Deleted (test import)                                   ││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ Selected Import Details:                                                │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ Import ID: abc-123-def-456                                          ││
│ │ Source: taivop/joke-dataset                                         ││
│ │ Imported: 2025-01-15 14:32:15                                       ││
│ │ Duration: 21m 48s                                                   ││
│ │                                                                      ││
│ │ Results:                                                             ││
│ │ • Total: 208,000  • Success: 199,234 (95.8%)  • Failed: 8,766      ││
│ │ • Pending: 199,234  • Approved: 0  • Rejected: 7,532               ││
│ │                                                                      ││
│ │ Actions:                                                             ││
│ │ [ Review (R) ] [ Merge (M) ] [ Export Report (E) ] [ Delete (D) ]  ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ [ Back (Esc) ]                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.4.2 Configuration Presets Manager

Save and manage import configurations.

```
┌─ Import Configuration Presets ──────────────────────────────────────────┐
│                                                                         │
│ ┌─ Saved Presets ──────────────────────────────────────────────────────┐│
│ │                                                                      ││
│ │ ► Quick Test (100 jokes)                                            ││
│ │   Max records: 100, Validation: ON, Auto-approve: OFF               ││
│ │   Use for: Testing new importers                                    ││
│ │                                                                      ││
│ │   Full Import (Default)                                             ││
│ │   Max records: None, Validation: ON, Batch: 100                     ││
│ │   Use for: Production imports                                       ││
│ │                                                                      ││
│ │   High Quality Only                                                  ││
│ │   Min score: 80, Maturity: G/PG, Auto-approve: ON                   ││
│ │   Use for: Family-friendly content                                  ││
│ │                                                                      ││
│ │   Development Mode                                                   ││
│ │   Max records: 1000, Validation: OFF, Fast mode                     ││
│ │   Use for: Development and debugging                                ││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ Selected Preset: Quick Test (100 jokes)                                │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ max_records: 100                                                    ││
│ │ validate: true                                                      ││
│ │ check_duplicates: false                                             ││
│ │ batch_size: 50                                                      ││
│ │ auto_approve_threshold: null                                        ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ [ Load (L) ] [ Edit (E) ] [ Delete (D) ] [ New Preset (N) ] [ Back ] │
└─────────────────────────────────────────────────────────────────────────┘
```

**Preset Storage:**
```yaml
# config/import_presets.yaml
presets:
  quick_test:
    name: "Quick Test (100 jokes)"
    description: "Use for testing new importers"
    config:
      max_records: 100
      validate: true
      check_duplicates: false
      batch_size: 50
      auto_approve_threshold: null

  full_import:
    name: "Full Import (Default)"
    description: "Use for production imports"
    config:
      max_records: null
      validate: true
      check_duplicates: true
      batch_size: 100

  high_quality:
    name: "High Quality Only"
    description: "Family-friendly content"
    config:
      max_records: null
      validate: true
      min_score: 80
      maturity_levels: ["G", "PG"]
      auto_approve_threshold: 85
```

---

## 4. Integration Between Import and Review TUIs

Seamless integration between import and review workflows.

### 4.1 Workflow Integration Points

```
┌─ Integrated Workflow ───────────────────────────────────────────────────┐
│                                                                         │
│ 1. IMPORT TUI                                                           │
│    ├─ Discovery Screen ─────► Select Importer                          │
│    ├─ Config Screen ────────► Configure Import                         │
│    ├─ Import Progress ──────► Live Stats                               │
│    └─ Summary Screen ───────► Results + Next Steps                     │
│                      │                                                  │
│                      ▼                                                  │
│ 2. AUTOMATIC HANDOFF                                                    │
│    • Import complete notification                                      │
│    • Show import statistics                                            │
│    • Prompt to start review                                            │
│                      │                                                  │
│                      ▼                                                  │
│ 3. REVIEW TUI                                                           │
│    ├─ Review Screen ─────────► Manual Review                           │
│    ├─ Policy Engine ─────────► Auto-Review                             │
│    ├─ Approve/Reject ─────────► Decision Making                        │
│    └─ Merge Complete ─────────► Production Database                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Shared Components

Both TUIs share common components for consistency:

```python
# src/joke_emporium/importers/tui/shared/
├── styles.py           # Shared CSS/theme
├── widgets.py          # Common widgets (progress bars, stats panels)
├── keybindings.py      # Consistent keyboard shortcuts
└── utils.py            # Shared utilities

# Example shared widget:
class StatsPanel(Static):
    """Shared statistics panel for both import and review TUIs."""

    def __init__(self, title: str):
        super().__init__()
        self.title = title

    def update_stats(self, stats: dict) -> None:
        """Update stats display (works for both import and review)."""
        self.update(f"""
┌─ {self.title} ─────────────────────────────────────────┐
│ Total: {stats['total']:,}                              │
│ Processed: {stats['processed']:,} ({stats['percent']:.1f}%)│
│ Successful: {stats['successful']:,}                    │
│ Failed: {stats['failed']:,}                            │
└────────────────────────────────────────────────────────┘
        """)
```

### 4.3 Cross-TUI Navigation

Enable easy switching between import and review modes:

```python
# Global keyboard shortcuts (available in both TUIs)
GLOBAL_BINDINGS = [
    ("ctrl+i", "open_import_tui", "Switch to Import"),
    ("ctrl+r", "open_review_tui", "Switch to Review"),
    ("ctrl+h", "open_history", "View History"),
    ("ctrl+s", "open_settings", "Settings"),
]

class BaseTUI(App):
    """Base class for both import and review TUIs."""

    def action_open_import_tui(self) -> None:
        """Switch to import TUI."""
        self.exit()
        from joke_emporium.importers.tui.import_app import ImportApp
        app = ImportApp()
        app.run()

    def action_open_review_tui(self) -> None:
        """Switch to review TUI."""
        self.exit()
        from joke_emporium.importers.tui.review_app import ReviewApp
        app = ReviewApp()
        app.run()
```

### 4.4 Unified CLI Entry Points

```bash
# Launch import TUI
uv run python -m joke_emporium.importers.cli tui import

# Launch review TUI
uv run python -m joke_emporium.importers.cli tui review

# Launch unified TUI hub (choose import or review)
uv run python -m joke_emporium.importers.cli tui

# Direct import + review workflow
uv run python -m joke_emporium.importers.cli tui workflow \
  --importer taivop \
  --auto-review \
  --merge-threshold 80
```

**Unified TUI Hub:**
```
┌─ Joke Emporium TUI Hub ─────────────────────────────────────────────────┐
│                                                                         │
│ What would you like to do?                                             │
│                                                                         │
│ ┌─ Quick Actions ──────────────────────────────────────────────────────┐│
│ │                                                                      ││
│ │ ► [I] Import New Data                                               ││
│ │   Download and import jokes from data sources                        ││
│ │   Last import: 2 hours ago (taivop, 199k jokes)                     ││
│ │                                                                      ││
│ │   [R] Review Imported Data                                           ││
│ │   Review and approve jokes in staging database                       ││
│ │   Pending review: 199,234 jokes across 1 import batch               ││
│ │                                                                      ││
│ │   [H] View History                                                   ││
│ │   Browse past imports and review sessions                            ││
│ │   Total imports: 5 | Total reviewed: 450,123 jokes                  ││
│ │                                                                      ││
│ │   [W] Run Workflow                                                   ││
│ │   Automated import + review + merge workflow                         ││
│ │   Recommended for high-quality data sources                          ││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ ┌─ System Status ──────────────────────────────────────────────────────┐│
│ │ Production DB: 123,456 jokes                                        ││
│ │ Staging DB: 199,234 pending | 7,532 rejected | 0 approved          ││
│ │ Disk Space: 1.2 GB used / 50 GB available                           ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│ [ Select Action ] [ Settings (S) ] [ Help (?) ] [ Quit (Q) ]          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Implementation Roadmap

### Sprint Breakdown

**Sprint 1: Core Import TUI (1 week)**
- [ ] Importer registry and auto-discovery
- [ ] Discovery screen with importer list
- [ ] Configuration screen with presets
- [ ] Download-only mode
- [ ] Basic import progress screen

**Sprint 2: Advanced Import Features (1 week)**
- [ ] Live progress with real-time stats
- [ ] Error tracking and reporting
- [ ] Summary screen with export options
- [ ] Import history browser
- [ ] Configuration preset manager

**Sprint 3: Review TUI Enhancements (1 week)**
- [ ] Split-pane view with context
- [ ] Quick rating system (1-5 keys)
- [ ] Smart filters with saved presets
- [ ] Policy engine integration
- [ ] Duplicate detection visualization

**Sprint 4: Integration and Polish (1 week)**
- [ ] Cross-TUI navigation
- [ ] Unified TUI hub
- [ ] Shared components and styles
- [ ] Accessibility improvements
- [ ] Documentation and help screens

### Dependencies

```toml
# Add to pyproject.toml
[project.dependencies]
textual = "^0.47.1"  # Modern TUI framework
rich = "^13.7.0"     # Already included
```

### Testing Strategy

```python
# tests/test_importers/test_tui/
├── test_discovery_screen.py
├── test_config_screen.py
├── test_import_progress.py
├── test_registry.py
└── test_integration.py

# Example test
async def test_importer_discovery():
    """Test importer auto-discovery."""
    ImporterRegistry.auto_discover()

    importers = ImporterRegistry.list_importers()
    assert len(importers) >= 1
    assert any(imp.name == "taivop" for imp in importers)

async def test_import_flow():
    """Test complete import flow in TUI."""
    app = ImportApp()

    # Select importer
    async with app.run_test() as pilot:
        await pilot.press("enter")  # Select first importer

        # Configure
        await pilot.press("enter")  # Use default config

        # Wait for import
        await pilot.pause(30)  # Adjust based on import size

        # Check summary
        assert "Import Complete" in app.screen.title
```

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| TUI Launch Time | < 2s | Auto-discovery + initial load |
| Import Start Time | < 1s | Config to start import |
| Progress Update Rate | 10 Hz | Real-time stats refresh |
| Memory Usage | < 200 MB | For 200k joke import |
| Screen Transition | < 100ms | Smooth navigation |

### Success Criteria

1. **Discoverability**: New importers automatically appear in TUI without code changes
2. **Usability**: First-time users can complete import without documentation
3. **Performance**: Import 200k jokes in < 30 minutes with live progress
4. **Integration**: Seamless handoff from import to review TUI
5. **Reliability**: Zero data loss even if TUI crashes mid-import

---

## Appendix: CLI Command Reference

### Import TUI Commands

```bash
# Launch import TUI (interactive mode)
uv run python -m joke_emporium.importers.cli tui import

# Launch with specific importer pre-selected
uv run python -m joke_emporium.importers.cli tui import --importer taivop

# Download-only mode
uv run python -m joke_emporium.importers.cli tui download --importer taivop

# Quick import with preset
uv run python -m joke_emporium.importers.cli tui import \
  --importer taivop \
  --preset quick_test
```

### Review TUI Commands

```bash
# Launch review TUI (interactive mode)
uv run python -m joke_emporium.importers.cli tui review

# Review specific import batch
uv run python -m joke_emporium.importers.cli tui review <import_id>

# Review with filters pre-applied
uv run python -m joke_emporium.importers.cli tui review <import_id> \
  --status pending \
  --min-score 70

# Review with theme
uv run python -m joke_emporium.importers.cli tui review <import_id> \
  --theme colorblind_safe
```

### Unified TUI Commands

```bash
# Launch TUI hub (choose import or review)
uv run python -m joke_emporium.importers.cli tui

# Complete workflow (import + review + merge)
uv run python -m joke_emporium.importers.cli tui workflow \
  --importer taivop \
  --max-records 1000 \
  --auto-review \
  --merge-threshold 80
```

---

## Summary

This document provides a comprehensive plan for:

1. **Review TUI Improvements**: Enhanced UX, performance, and accessibility
2. **Future Enhancements**: Advanced features for long-term value
3. **Import TUI Design**: Complete interactive import workflow
4. **Integration**: Seamless connection between import and review

**Key Benefits:**
- **Developer Experience**: Transform tedious CLI workflows into efficient interactive TUIs
- **Productivity**: 3-5x faster review and import processes
- **Quality**: Better data quality through intuitive review interface
- **Scalability**: Handle 50k+ jokes with ease
- **Accessibility**: Keyboard-only navigation, screen reader support, colorblind themes

**Next Steps:**
1. Review and approve this design document
2. Create feature branches for each sprint
3. Begin Sprint 1: Core Import TUI
4. Parallel development: Import TUI (Sprint 1-2) and Review TUI improvements (Sprint 3)
5. Integration and testing (Sprint 4)

**Estimated Timeline:** 4 weeks total (1 week per sprint)

**Dependencies:**
- Textual framework (already decided)
- Shared component library
- Import registry system
- Cross-TUI navigation framework

# BrainCell Web Dashboard

A modern web interface for viewing and managing BrainCell memory system. The dashboard provides visualization and search capabilities across all stored knowledge.

## Features

- **Overview Dashboard** - High-level statistics and recent activity
- **Conversations View** - Browse and search conversation history
- **Decisions View** - View design decisions with rationale and impact
- **Architecture Notes** - Explore system design and component documentation
- **Code Snippets** - Reusable code examples with language filtering
- **Unified Search** - Search across all memory types simultaneously
- **Responsive Design** - Works on desktop, tablet, and mobile devices

## Accessing the Dashboard

Once the BrainCell API is running (port 8000), access the dashboard at:

```
http://localhost:8000/dashboard/
```

### Dashboard Pages

| URL | Purpose |
|-----|---------|
| `/dashboard/` | Overview with statistics and recent items |
| `/dashboard/conversations` | List all conversations |
| `/dashboard/decisions` | List all design decisions |
| `/dashboard/architecture-notes` | List all architecture documentation |
| `/dashboard/code-snippets` | List all code examples |
| `/dashboard/search` | Universal search across all types |

## Features by Page

### Overview Dashboard (`/dashboard/`)
- Statistics cards showing totals for each memory type
- Recent conversations, decisions, notes, and snippets
- Quick links to detailed pages
- Interactive cards with hover effects

### Conversations (`/dashboard/conversations`)
- Complete conversation history
- Search by topic
- Pagination support
- Timestamp and session information
- Summary preview for each conversation

### Decisions (`/dashboard/decisions`)
- Design decisions with rationale and impact
- Filter by status (active, archived, superseded)
- Search functionality
- Color-coded status badges
- Date information

### Architecture Notes (`/dashboard/architecture-notes`)
- System design and pattern documentation
- Filter by type (general, pattern, integration, constraint)
- Search by component or description
- Tag support
- Component-based organization

### Code Snippets (`/dashboard/code-snippets`)
- Reusable code examples
- Filter by programming language
- Code preview in cards
- File path references
- Language syntax indication

### Search (`/dashboard/search`)
- Search across all memory types simultaneously
- Displays results organized by type
- Minimum 3 characters required
- Instant filtering

## Design & Styling

The dashboard uses:
- **Bootstrap 5.3.2** - Responsive grid and components
- **Custom CSS** - Brand styling with purple accent color (#7c3aed)
- **Google Fonts** - Poppins and Raleway for typography
- **Bootstrap Icons** - Consistent iconography

### Color Scheme

```css
--primary-color: #0d6efd       (Bootstrap Blue)
--accent-color: #7c3aed        (BrainCell Purple)
--success-color: #28a745       (Green)
--warning-color: #ffc107       (Yellow)
--danger-color: #dc3545        (Red)
--header-bg: #1a1a2e           (Dark Blue)
--background-color: #f8f9fa    (Light Gray)
```

## Responsive Design

The dashboard is fully responsive:

- **Desktop** (>992px): Full layout with sidebar navigation
- **Tablet** (768px-991px): Adapted grid layout
- **Mobile** (<768px): Single column layout with stacked navigation

## Technical Details

### Routes Module
Located in `src/web/router.py`, provides:
- `/dashboard/` - Main overview endpoint
- `/dashboard/conversations` - Conversations list
- `/dashboard/decisions` - Design decisions list
- `/dashboard/architecture-notes` - Architecture notes list
- `/dashboard/code-snippets` - Code snippets list
- `/dashboard/search` - Universal search

### Templates
Located in `src/web/templates/`:
- `base.html` - Base layout with header and navigation
- `dashboard.html` - Overview page
- `conversations.html` - Conversations listing
- `decisions.html` - Decisions listing
- `architecture_notes.html` - Architecture notes listing
- `code_snippets.html` - Code snippets listing
- `search.html` - Search results page

### Static Files
Located in `src/web/static/`:
- `css/braincell.css` - Custom styles and animations
- Additional CSS and JavaScript can be added here

## Integration with API

The dashboard reads data from:
- PostgreSQL database (via SQLAlchemy ORM)
- All major entity types from the BrainCell data model
- Real-time data without caching

## Usage Scenarios

### Reviewing Decisions
1. Navigate to `/dashboard/decisions`
2. Filter by status or search by topic
3. View rationale and impact for each decision

### Finding Code Examples
1. Go to `/dashboard/code-snippets`
2. Filter by programming language
3. Review code preview and file references
4. Copy snippets as needed

### Understanding Architecture
1. Visit `/dashboard/architecture-notes`
2. Filter by component type
3. Review system design patterns and constraints
4. Track architectural evolution

### Searching Knowledge
1. Go to `/dashboard/search`
2. Enter search term (3+ characters)
3. Review results grouped by type
4. Navigate to specific items for details

## Performance

- Pagination limits to 20 items per page by default
- Database queries are optimized with proper indexing
- Search is case-insensitive and performs substring matching
- Client-side filtering for instant response

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Future Enhancements

Potential additions:
- Export functionality (PDF, CSV)
- Advanced filtering and complex queries
- Favorites/bookmarking system
- Tags and custom categorization
- Dark mode toggle
- Real-time updates via WebSocket
- Dashboard customization
- User preferences and bookmarks

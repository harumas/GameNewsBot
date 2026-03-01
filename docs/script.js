/**
 * Game News Bot - Frontend Script
 * Fetches news.json and renders categorized articles
 */

// Category definitions (must match Python categorizer.py)
const CATEGORIES = {
    release: { emoji: '🎮', label: '新作・リリース' },
    sale: { emoji: '💰', label: 'セール・キャンペーン' },
    update: { emoji: '🔧', label: 'アップデート・DLC' },
    tech: { emoji: '⚙️', label: '技術・開発' },
    cg: { emoji: '🎨', label: 'CG・アート' },
    business: { emoji: '💼', label: 'ビジネス' },
    industry: { emoji: '📢', label: '業界ニュース' },
    esports: { emoji: '🏆', label: 'eスポーツ・配信' },
    other: { emoji: '📰', label: 'その他' },
};

const CATEGORY_ORDER = [
    'release', 'sale', 'update', 'tech', 'cg',
    'business', 'industry', 'esports', 'other',
];

// Source name → CSS class mapping
function getSourceClass(source) {
    const map = {
        '4Gamer.net': 'source-4gamer',
        'Automaton': 'source-automaton',
        'IGN Japan': 'source-ign',
        'ファミ通.com': 'source-famitsu',
        'ゲームメーカーズ': 'source-gamemakers',
        '電ファミニコゲーマー': 'source-denfami',
        'Unity Japan': 'source-unity',
        'CGWORLD': 'source-cgworld',
        'GameBusiness.jp': 'source-gamebiz',
    };
    return map[source] || '';
}

// Format date string
function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    const month = d.getMonth() + 1;
    const day = d.getDate();
    return `${month}/${day}`;
}

// Format the generated_at timestamp
function formatGeneratedAt(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    const y = d.getFullYear();
    const m = d.getMonth() + 1;
    const day = d.getDate();
    const hours = String(d.getHours()).padStart(2, '0');
    const mins = String(d.getMinutes()).padStart(2, '0');
    return `${y}年${m}月${day}日 ${hours}:${mins} 更新`;
}

// Group articles by category
function groupByCategory(articles) {
    const groups = {};
    for (const article of articles) {
        const cat = article.category || 'other';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(article);
    }
    return groups;
}

// Create an article card element
function createArticleCard(article) {
    const card = document.createElement('a');
    card.className = `article-card${article.importance === 'high' ? ' importance-high' : ''}`;

    // Mark as featured duplicate if it's currently featured
    if (window._featuredUrls && window._featuredUrls.has(article.url)) {
        card.classList.add('featured-duplicate');
    }

    card.href = article.url;
    card.target = '_blank';
    card.rel = 'noopener noreferrer';

    const sourceClass = getSourceClass(article.source);
    const timeStr = formatDate(article.published);

    const imgHtml = article.image
        ? `<div class="article-thumb"><img src="${escapeHtml(article.image)}" alt="" loading="lazy" onerror="this.parentElement.style.display='none'"></div>`
        : '';

    card.innerHTML = `
        ${imgHtml}
        <div class="article-info">
            <div class="article-title">${escapeHtml(article.title)}</div>
            <div class="article-meta">
                <span class="article-source ${sourceClass}">${escapeHtml(article.source)}</span>
                ${timeStr ? `<span class="article-time">🕐 ${timeStr}</span>` : ''}
            </div>
        </div>
        <span class="article-arrow">→</span>
    `;

    return card;
}

// Create a category group element
function createCategoryGroup(category, articles) {
    const cat = CATEGORIES[category] || CATEGORIES.other;

    const group = document.createElement('div');
    group.className = 'category-group';
    group.dataset.category = category;

    // Sort: high importance first, then by date (newest first)
    articles.sort((a, b) => {
        if (a.importance !== b.importance) {
            return a.importance === 'high' ? -1 : 1;
        }
        const da = new Date(a.published || 0);
        const db = new Date(b.published || 0);
        return db - da;
    });

    group.innerHTML = `
        <div class="category-header">
            <span class="category-icon">${cat.emoji}</span>
            <span class="category-name">${cat.label}</span>
            <span class="category-count">${articles.length}件</span>
        </div>
        <div class="article-list"></div>
    `;

    const list = group.querySelector('.article-list');

    // Only show up to 3 articles per category
    const displayArticles = articles.slice(0, 3);
    for (const article of displayArticles) {
        list.appendChild(createArticleCard(article));
    }

    return group;
}

// Escape HTML to prevent XSS
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// --- Filter logic ---
let activeFilter = 'all';

function setupFilters(groups) {
    const filterBar = document.getElementById('filter-bar');
    if (!filterBar) return;

    filterBar.innerHTML = '';

    // "All" button
    const allBtn = document.createElement('button');
    allBtn.className = 'filter-btn active';
    allBtn.textContent = 'すべて';
    allBtn.dataset.filter = 'all';
    allBtn.addEventListener('click', () => setFilter('all'));
    filterBar.appendChild(allBtn);

    // Category buttons (only for categories that have articles)
    for (const cat of CATEGORY_ORDER) {
        if (!groups[cat] || groups[cat].length === 0) continue;
        const info = CATEGORIES[cat] || CATEGORIES.other;
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.textContent = `${info.emoji} ${info.label}`;
        btn.dataset.filter = cat;
        btn.addEventListener('click', () => setFilter(cat));
        filterBar.appendChild(btn);
    }
}

function setFilter(category) {
    activeFilter = category;

    // Update button state
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === category);
    });

    // Show/hide category groups
    document.querySelectorAll('.category-group').forEach(group => {
        if (category === 'all' || group.dataset.category === category) {
            group.classList.remove('hidden');
        } else {
            group.classList.add('hidden');
        }
    });

    // Hide featured duplicates in the 'all' view, but show them in specific categories
    document.querySelectorAll('.featured-duplicate').forEach(card => {
        card.style.display = category === 'all' ? 'none' : '';
    });

    // Hide the featured section entirely when not in 'all' view
    const featuredSection = document.getElementById('featured-section');
    if (featuredSection && window._featuredUrls && window._featuredUrls.size > 0) {
        featuredSection.style.display = category === 'all' ? '' : 'none';
    }
}

// --- Events Calendar logic ---

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'];
const MONTH_NAMES = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

function getCountdownInfo(startStr, endStr) {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const start = new Date(startStr);
    start.setHours(0, 0, 0, 0);
    const end = new Date(endStr);
    end.setHours(23, 59, 59, 999);

    if (now > end) {
        return { text: '終了', cssClass: 'ended', isPast: true };
    }
    if (now >= start && now <= end) {
        return { text: '開催中！', cssClass: 'ongoing', isPast: false };
    }

    const diffMs = start - now;
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays <= 30) {
        return { text: `あと${diffDays}日`, cssClass: 'soon', isPast: false };
    }
    return { text: `あと${diffDays}日`, cssClass: 'upcoming', isPast: false };
}

function createCalendarEvent(event) {
    const countdown = getCountdownInfo(event.date_start, event.date_end);
    const start = new Date(event.date_start);
    const end = new Date(event.date_end);
    const startDay = start.getDate();
    const startWeekday = WEEKDAYS[start.getDay()];

    // Multi-day range text
    let rangeText = '';
    if (event.date_start !== event.date_end) {
        const endDay = end.getDate();
        if (start.getMonth() === end.getMonth()) {
            rangeText = `〜${endDay}日`;
        } else {
            rangeText = `〜${end.getMonth() + 1}/${endDay}`;
        }
    }

    const tagsHtml = (event.tags || [])
        .map(t => `<span class="cal-tag">${escapeHtml(t)}</span>`)
        .join('');

    const row = document.createElement('a');
    row.className = `cal-event${countdown.isPast ? ' event-past' : ''}`;
    row.href = event.url || '#';
    row.target = '_blank';
    row.rel = 'noopener noreferrer';

    row.innerHTML = `
        <div class="cal-date">
            <div class="cal-date-day">${startDay}</div>
            <div class="cal-date-weekday">${startWeekday}</div>
            ${rangeText ? `<div class="cal-date-range">${rangeText}</div>` : ''}
        </div>
        <div class="cal-event-info">
            <div class="cal-event-name">${escapeHtml(event.name)}</div>
            <div class="cal-event-detail">
                <span class="cal-event-venue">📍 ${escapeHtml(event.venue || event.location)}</span>
                <div class="cal-tags">${tagsHtml}</div>
            </div>
        </div>
        <span class="cal-countdown ${countdown.cssClass}">${countdown.text}</span>
    `;

    return row;
}

function createMonthGroup(monthNum, year, events) {
    const group = document.createElement('div');
    group.className = 'cal-month';

    const headerHtml = `
        <div class="cal-month-header">
            <span class="cal-month-num m${monthNum}">${monthNum}</span>
            <span class="cal-month-label">${year}年${MONTH_NAMES[monthNum - 1]}</span>
            <span class="cal-event-count">${events.length}件</span>
        </div>
    `;

    group.innerHTML = headerHtml;

    const list = document.createElement('div');
    list.className = 'cal-event-list';
    for (const event of events) {
        list.appendChild(createCalendarEvent(event));
    }
    group.appendChild(list);

    return group;
}

async function loadEvents() {
    const section = document.getElementById('events-section');
    const calendar = document.getElementById('events-calendar');
    if (!section || !calendar) return;

    try {
        const resp = await fetch('data/events.json');
        if (!resp.ok) return;
        const data = await resp.json();

        const events = data.events || [];
        if (events.length === 0) return;

        // Sort by start date
        events.sort((a, b) => new Date(a.date_start) - new Date(b.date_start));

        // Group by month
        const months = new Map();
        for (const event of events) {
            const d = new Date(event.date_start);
            const key = `${d.getFullYear()}-${d.getMonth() + 1}`;
            if (!months.has(key)) {
                months.set(key, { year: d.getFullYear(), month: d.getMonth() + 1, events: [] });
            }
            months.get(key).events.push(event);
        }

        calendar.innerHTML = '';
        for (const [, monthData] of months) {
            calendar.appendChild(createMonthGroup(monthData.month, monthData.year, monthData.events));
        }

        section.style.display = '';
    } catch (err) {
        console.warn('Failed to load events:', err);
    }
}

// --- Main render function ---
async function init() {
    const newsContainer = document.getElementById('news-container');
    const poemText = document.getElementById('poem-text');
    const poemSection = document.getElementById('poem-section');
    const lastUpdated = document.getElementById('last-updated');

    // Load events in parallel
    loadEvents();

    try {
        const resp = await fetch('data/news.json?t=' + Date.now());
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        // Update last updated time
        if (data.generated_at && lastUpdated) {
            lastUpdated.innerHTML = `
                <span class="pulse-dot"></span>
                ${formatGeneratedAt(data.generated_at)}
            `;
        }

        // Show poem
        if (data.poem && poemText) {
            poemText.textContent = data.poem;
            poemSection.style.display = '';
        } else if (poemSection) {
            poemSection.style.display = 'none';
        }

        // Group and render articles
        const articles = data.articles || [];
        if (articles.length === 0) {
            newsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <div class="empty-text">現在表示できるニュースはありません</div>
                </div>
            `;
            return;
        }

        const groups = groupByCategory(articles);
        setupFilters(groups);

        // ---- Featured (high importance) articles ----
        const featuredSection = document.getElementById('featured-section');
        const featuredGrid = document.getElementById('featured-grid');
        const featured = articles.filter(a => a.importance === 'high').slice(0, 3);

        // Track featured URLs globally so createArticleCard can mark them as duplicates
        window._featuredUrls = new Set(featured.map(a => a.url));

        if (featured.length > 0 && featuredSection && featuredGrid) {
            featuredGrid.innerHTML = '';
            for (const article of featured) {
                const cat = CATEGORIES[article.category] || CATEGORIES.other;
                const date = article.published ? formatDate(article.published) : '';
                const sourceClass = getSourceClass(article.source);

                const card = document.createElement('a');
                card.className = 'featured-card';
                card.href = article.url;
                card.target = '_blank';
                card.rel = 'noopener noreferrer';

                const imgHtml = article.image
                    ? `<div class="featured-img"><img src="${escapeHtml(article.image)}" alt="" loading="lazy" onerror="this.parentElement.style.display='none'"></div>`
                    : '';

                card.innerHTML = `
                    ${imgHtml}
                    <div class="featured-card-body">
                        <span class="featured-badge">${escapeHtml(cat.emoji)} ${escapeHtml(cat.label)}</span>
                        <h3 class="featured-card-title">${escapeHtml(article.title)}</h3>
                        <div class="featured-card-meta">
                            <span class="article-source ${sourceClass}">${escapeHtml(article.source)}</span>
                            <span>${date}</span>
                        </div>
                    </div>
                `;
                featuredGrid.appendChild(card);
            }
            featuredSection.style.display = '';
        }

        // ---- Category groups ----
        newsContainer.innerHTML = '';
        for (const cat of CATEGORY_ORDER) {
            if (!groups[cat] || groups[cat].length === 0) continue;
            newsContainer.appendChild(createCategoryGroup(cat, groups[cat]));
        }

        // Apply initial filter to hide featured duplicates
        setFilter('all');

    } catch (err) {
        console.error('Failed to load news:', err);
        newsContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <div class="empty-text">ニュースの読み込みに失敗しました<br>しばらく経ってからリロードしてください</div>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', init);

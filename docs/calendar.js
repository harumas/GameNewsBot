/**
 * Interactive Event Calendar Script
 * Reads docs/data/events.json and renders a dynamic monthly calendar grid.
 */

let currentDate = new Date();
let eventsData = [];
let holidaysData = {}; // Format: { "YYYY-MM-DD": "Holiday Name" }

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    fetchHolidaysAndEvents();
});

function setupEventListeners() {
    document.getElementById('prev-month-btn').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });

    document.getElementById('next-month-btn').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
}

// --- Data Fetching ---
async function fetchHolidaysAndEvents() {
    try {
        // Fetch Japanese Public Holidays API (Thanks to holidays-jp)
        const currentYear = currentDate.getFullYear();
        const holidayRes = await fetch('https://holidays-jp.github.io/api/v1/date.json');
        if (holidayRes.ok) {
            holidaysData = await holidayRes.json();
        }

        // Fetch our static events
        const eventRes = await fetch('data/events.json');
        if (eventRes.ok) {
            const data = await eventRes.json();
            eventsData = data.events || [];
        }
    } catch (e) {
        console.error("Failed to load calendar data:", e);
    }

    renderCalendar();
}

// --- Helper Functions ---
function getMonthName(date) {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    return `${year}年 ${month}月`;
}

function formatDateKey(year, month, day) {
    // Returns YYYY-MM-DD
    const m = String(month).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    return `${year}-${m}-${d}`;
}

// --- Rendering Logic ---
function renderCalendar() {
    document.getElementById('current-month-display').textContent = getMonthName(currentDate);

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    // Get number of days in the month and what day of the week the 1st falls on
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = ''; // Clear existing days

    const today = new Date();
    const isCurrentMonth = (today.getFullYear() === year && today.getMonth() === month);

    // 1. Fill empty slots before the 1st of the month
    for (let i = 0; i < firstDay; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'calendar-day empty';
        emptyCell.style.background = 'transparent';
        emptyCell.style.border = 'none';
        grid.appendChild(emptyCell);
    }

    // 2. Render actual days
    for (let day = 1; day <= daysInMonth; day++) {
        const dateKey = formatDateKey(year, month + 1, day);

        const cell = document.createElement('div');
        cell.className = 'calendar-day';

        // Setup Date Header
        const dateHeader = document.createElement('div');
        dateHeader.className = 'calendar-date-header';

        const dateNumber = document.createElement('span');
        dateNumber.className = 'calendar-date-number';
        dateNumber.textContent = day;

        // Highlight Today
        if (isCurrentMonth && today.getDate() === day) {
            cell.classList.add('is-today');
        }

        // Highlight Japanese Holidays
        const holidayName = holidaysData[dateKey];
        if (holidayName) {
            cell.classList.add('is-holiday');
            const holidaySpan = document.createElement('span');
            holidaySpan.className = 'holiday-name';
            holidaySpan.textContent = holidayName;
            dateHeader.appendChild(holidaySpan);
        }

        // Sunday styling (0 = Sunday, 6 = Saturday) based on column position
        const currentDow = (firstDay + day - 1) % 7;
        if (currentDow === 0) { cell.classList.add('is-sunday'); }
        if (currentDow === 6) { cell.classList.add('is-saturday'); }

        dateHeader.prepend(dateNumber);
        cell.appendChild(dateHeader);

        // Render Events
        const eventsContainer = document.createElement('div');
        eventsContainer.className = 'calendar-events-list';

        // Filter events that fall on this day (inclusive of multi-day events)
        const dayEvents = eventsData.filter(event => {
            if (!event.date_start) return false;

            // Single day check or multi-day range check
            if (event.date_end) {
                return dateKey >= event.date_start && dateKey <= event.date_end;
            } else {
                return event.date_start.startsWith(dateKey);
            }
        });

        dayEvents.forEach(event => {
            const evPill = document.createElement('a');

            // Map event tags to colors
            let colorTag = 'gaming';
            if (event.tags) {
                if (event.tags.includes('海外')) colorTag = 'presentation';
                if (event.tags.includes('出展可能')) colorTag = 'release';
                if (event.tags.includes('同人')) colorTag = 'sale';
                if (event.tags.includes('カンファレンス')) colorTag = 'esports';
            }

            evPill.className = `calendar-event-pill tag-${colorTag}`;
            evPill.href = event.url || '#';
            evPill.target = '_blank';
            evPill.rel = 'noopener noreferrer';

            // Visual indicator if this is a continuation of a multi-day event
            const isContinuation = event.date_start && event.date_end && dateKey > event.date_start;
            if (isContinuation) {
                evPill.style.borderLeftStyle = 'dashed';
            }

            // Build Tooltip HTML
            const locationText = event.venue ? `${event.location} (${event.venue})` : event.location;
            const tooltipHTML = `
                <div class="calendar-tooltip">
                    <div class="tooltip-title">${escapeHtml(event.name)}</div>
                    ${event.date_start ? `<div class="tooltip-date">📅 ${event.date_start}${event.date_end && event.date_start !== event.date_end ? ' 〜 ' + event.date_end : ''}</div>` : ''}
                    ${locationText ? `<div class="tooltip-location">📍 ${escapeHtml(locationText)}</div>` : ''}
                    ${event.description ? `<div class="tooltip-desc">${escapeHtml(event.description)}</div>` : ''}
                </div>
            `;

            evPill.innerHTML = `
                <span class="event-title">${escapeHtml(event.name)}</span>
                ${tooltipHTML}
            `;
            eventsContainer.appendChild(evPill);
        });

        cell.appendChild(eventsContainer);
        grid.appendChild(cell);
    }
}

// Simple local HTML escaper 
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

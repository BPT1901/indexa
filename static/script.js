// Global variables
let searchTimeout;
let currentSearchQuery = '';

// DOM elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const categoryFilter = document.getElementById('categoryFilter');
const clearSearchBtn = document.getElementById('clearSearch');
const searchResults = document.getElementById('searchResults');
const recentEntries = document.getElementById('recentEntries');
const entriesList = document.getElementById('entriesList');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    loadRecentEntries();
    setupEventListeners();
    setupKeyboardShortcuts();
});

// Event listeners
function setupEventListeners() {
    searchInput.addEventListener('input', handleSearchInput);
    searchBtn.addEventListener('click', performSearch);
    clearSearchBtn.addEventListener('click', clearSearch);
    categoryFilter.addEventListener('change', performSearch);
    
    // Handle Enter key in search
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+K or Cmd+K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
        
        // Escape to clear search
        if (e.key === 'Escape') {
            clearSearch();
        }
        
        // Show shortcuts on ?
        if (e.key === '?' && !e.target.matches('input, textarea')) {
            showShortcuts();
        }
    });
}

// Search functionality
function handleSearchInput() {
    clearTimeout(searchTimeout);
    const query = searchInput.value.trim();
    
    if (query.length > 0) {
        searchTimeout = setTimeout(() => {
            performSearch();
        }, 300); // Debounce search
    } else {
        clearSearch();
    }
}

async function performSearch() {
    const query = searchInput.value.trim();
    const category = categoryFilter.value;
    
    if (!query) {
        clearSearch();
        return;
    }
    
    try {
        showLoading(searchResults);
        
        const params = new URLSearchParams({
            q: query,
            limit: '20'
        });
        
        if (category) {
            params.append('category', category);
        }
        
        const response = await fetch(`/search?${params}`);
        const results = await response.json();
        
        displaySearchResults(results);
        currentSearchQuery = query;
        
        // Hide recent entries when showing search results
        recentEntries.style.display = 'none';
        
    } catch (error) {
        console.error('Search error:', error);
        searchResults.innerHTML = '<div class="no-results">Error performing search. Please try again.</div>';
    }
}

function displaySearchResults(results) {
    searchResults.innerHTML = '';
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="no-results">No results found for your search.</div>';
        return;
    }
    
    const resultsTitle = document.createElement('h2');
    resultsTitle.textContent = `Search Results (${results.length})`;
    searchResults.appendChild(resultsTitle);
    
    results.forEach(result => {
        const entryCard = createEntryCard(result, true);
        searchResults.appendChild(entryCard);
    });
}

function clearSearch() {
    searchInput.value = '';
    categoryFilter.value = '';
    searchResults.innerHTML = '';
    currentSearchQuery = '';
    recentEntries.style.display = 'block';
    searchInput.focus();
}

// Load categories for filter dropdown
async function loadCategories() {
    try {
        const response = await fetch('/categories');
        const categories = await response.json();
        
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Load recent entries
async function loadRecentEntries() {
    try {
        showLoading(entriesList);
        
        const response = await fetch('/entries?limit=3');
        const entries = await response.json();
        
        displayEntries(entries);
    } catch (error) {
        console.error('Error loading recent entries:', error);
        entriesList.innerHTML = '<div class="no-results">Error loading entries.</div>';
    }
}

function displayEntries(entries) {
    entriesList.innerHTML = '';
    
    if (entries.length === 0) {
        entriesList.innerHTML = '<div class="no-results">No entries found. <a href="/add">Add your first entry!</a></div>';
        return;
    }
    
    entries.forEach(entry => {
        const entryCard = createEntryCard(entry, false);
        entriesList.appendChild(entryCard);
    });
}

// Create entry card HTML
function createEntryCard(entry, isSearchResult = false) {
    const card = document.createElement('div');
    card.className = 'entry-card';
    
    const tags = entry.tags ? entry.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
    const tagsHTML = tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('');
    
    const snippetHTML = isSearchResult && entry.snippet ? 
        `<div class="entry-snippet">${entry.snippet}</div>` : '';
    
    const contentPreview = !isSearchResult ? 
        `<div class="entry-snippet">${escapeHtml(entry.content.substring(0, 150))}${entry.content.length > 150 ? '...' : ''}</div>` : '';
    
    card.innerHTML = `
        <div class="entry-title">
            <a href="/view/${entry.id}">${escapeHtml(entry.title)}</a>
        </div>
        <div class="entry-meta">
            <span class="entry-category">${escapeHtml(entry.category)}</span>
            <span>Updated: ${formatDate(entry.updated_at)}</span>
        </div>
        ${tagsHTML ? `<div class="entry-tags">${tagsHTML}</div>` : ''}
        ${snippetHTML || contentPreview}
        <div class="entry-actions">
            <a href="/view/${entry.id}" class="btn-small btn-view"><i class="fas fa-eye"></i> View</a>
            <a href="/edit/${entry.id}" class="btn-small btn-edit"><i class="fas fa-edit"></i> Edit</a>
            <button onclick="deleteEntry(${entry.id})" class="btn-small btn-delete"><i class="fas fa-trash"></i> Delete</button>
            <button onclick="copyToClipboard('${entry.id}')" class="btn-small btn-secondary"><i class="fas fa-copy"></i> Copy</button>
        </div>
    `;
    
    return card;
}

// Delete entry
async function deleteEntry(entryId) {
    if (!confirm('Are you sure you want to delete this entry?')) {
        return;
    }
    
    try {
        const response = await fetch(`/entries/${entryId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Refresh the current view
            if (currentSearchQuery) {
                performSearch();
            } else {
                loadRecentEntries();
            }
            showNotification('Entry deleted successfully', 'success');
        } else {
            showNotification('Error deleting entry', 'error');
        }
    } catch (error) {
        console.error('Error deleting entry:', error);
        showNotification('Error deleting entry', 'error');
    }
}

// Copy entry content to clipboard
async function copyToClipboard(entryId) {
    try {
        const response = await fetch(`/entries/${entryId}`);
        const entry = await response.json();
        
        await navigator.clipboard.writeText(entry.content);
        showNotification('Content copied to clipboard', 'success');
    } catch (error) {
        console.error('Error copying to clipboard:', error);
        showNotification('Error copying to clipboard', 'error');
    }
}

// Utility functions
function showLoading(container) {
    container.innerHTML = '<div class="loading">Loading...</div>';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add notification styles if not already present
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                animation: slideIn 0.3s ease-out;
            }
            .notification.success { background: #28a745; }
            .notification.error { background: #dc3545; }
            .notification.info { background: #17a2b8; }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function showShortcuts() {
    const shortcuts = document.createElement('div');
    shortcuts.className = 'shortcuts show';
    shortcuts.innerHTML = `
        <div><kbd>Ctrl+K</kbd> Focus search</div>
        <div><kbd>Esc</kbd> Clear search</div>
        <div><kbd>?</kbd> Show shortcuts</div>
    `;
    
    document.body.appendChild(shortcuts);
    
    setTimeout(() => {
        shortcuts.remove();
    }, 3000);
}

// Handle code block copy buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('copy-btn')) {
        const codeBlock = e.target.parentElement;
        const code = codeBlock.textContent.replace('Copy', '').trim();
        
        navigator.clipboard.writeText(code).then(() => {
            e.target.textContent = 'Copied!';
            setTimeout(() => {
                e.target.textContent = 'Copy';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    }
});
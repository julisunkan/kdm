// KDP Keyword Research Tool - Main JavaScript Application

class KDPKeywordTool {
    constructor() {
        this.currentResults = [];
        this.favorites = new Set();
        this.currentSession = null;
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupTheme();
        this.loadFavorites();
        this.loadAutoSaveSession();
    }
    
    setupEventListeners() {
        // Search form
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }
        
        // Bulk mode toggle
        const bulkToggle = document.getElementById('bulkMode');
        if (bulkToggle) {
            bulkToggle.addEventListener('change', (e) => this.toggleBulkMode(e));
        }
        
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // Export buttons
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleExport(e));
        });
        
        // Session management
        const saveSessionBtn = document.getElementById('saveSession');
        if (saveSessionBtn) {
            saveSessionBtn.addEventListener('click', () => this.showSaveSessionForm());
        }
        
        // Save session form handlers
        const confirmSaveBtn = document.getElementById('confirmSaveSession');
        const cancelSaveBtn = document.getElementById('cancelSaveSession');
        const sessionNameInput = document.getElementById('sessionNameInput');
        
        if (confirmSaveBtn) {
            confirmSaveBtn.addEventListener('click', () => this.saveSession());
        }
        
        if (cancelSaveBtn) {
            cancelSaveBtn.addEventListener('click', () => this.hideSaveSessionForm());
        }
        
        if (sessionNameInput) {
            sessionNameInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.saveSession();
                }
            });
        }
        
        // Filters
        this.setupFilters();
        
        // Copy buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('copy-btn')) {
                this.copyToClipboard(e.target.dataset.keyword);
            }
        });
        
        // Favorite buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('favorite-btn')) {
                this.toggleFavorite(e.target.dataset.keyword, e.target);
            }
        });
    }
    
    setupTheme() {
        // Load saved theme or detect system preference
        const savedTheme = localStorage.getItem('kdp-theme');
        const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (systemDark ? 'dark' : 'light');
        
        this.setTheme(theme);
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('kdp-theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
    
    setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('kdp-theme', theme);
        
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.innerHTML = theme === 'dark' ? 
                '<i class="fas fa-sun"></i>' : 
                '<i class="fas fa-moon"></i>';
        }
    }
    
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
    
    toggleBulkMode(e) {
        const textarea = document.getElementById('keywordsInput');
        const helpText = document.querySelector('.bulk-mode-label');
        
        if (e.target.checked) {
            textarea.placeholder = 'Enter keywords, one per line:\nkeyword 1\nkeyword 2\nkeyword 3';
            helpText.textContent = 'Bulk mode: Enter one keyword per line';
        } else {
            textarea.placeholder = 'Enter keywords separated by commas: keyword 1, keyword 2, keyword 3';
            helpText.textContent = 'Single mode: Enter keywords separated by commas';
        }
    }
    
    async handleSearch(e) {
        e.preventDefault();
        
        const keywordsInput = document.getElementById('keywordsInput');
        const bulkMode = document.getElementById('bulkMode').checked;
        const submitBtn = e.target.querySelector('button[type="submit"]');
        
        if (!keywordsInput.value.trim()) {
            this.showToast('Please enter some keywords', 'warning');
            return;
        }
        
        // Show loading state
        this.setLoadingState(submitBtn, true);
        
        try {
            const response = await fetch('/search_keywords', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keywords: keywordsInput.value,
                    bulk_mode: bulkMode
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentResults = data.results;
                this.displayResults(data.results);
                this.updateCharts(data.results);
                this.showToast(`Found ${data.total_keywords} keyword results`, 'success');
            } else {
                this.showToast(data.error || 'Search failed', 'error');
            }
            
        } catch (error) {
            console.error('Search error:', error);
            this.showToast('Search failed. Please try again.', 'error');
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }
    
    displayResults(results) {
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsTable = document.getElementById('resultsTable');
        
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="alert alert-info">No results found. Try different keywords.</div>';
            return;
        }
        
        // Create table HTML
        let tableHTML = `
            <div class="table-responsive">
                <table class="table table-striped table-hover results-table">
                    <thead class="table-dark">
                        <tr>
                            <th>Keyword</th>
                            <th>Search Volume</th>
                            <th>Difficulty</th>
                            <th>Profitability</th>
                            <th>Amazon Results</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        results.forEach(result => {
            const difficultyColor = this.getScoreColor(result.difficulty_score, true);
            const profitabilityColor = this.getScoreColor(result.profitability_score, false);
            const isFavorite = this.favorites.has(result.keyword);
            
            tableHTML += `
                <tr class="fade-in">
                    <td class="keyword-cell" title="${result.keyword}">${result.keyword}</td>
                    <td>${result.search_volume || 0}</td>
                    <td><span class="badge bg-${difficultyColor}">${(result.difficulty_score || 0).toFixed(1)}</span></td>
                    <td><span class="badge bg-${profitabilityColor}">${(result.profitability_score || 0).toFixed(1)}</span></td>
                    <td>${(result.amazon_results || 0).toLocaleString()}</td>
                    <td>
                        <button class="btn btn-sm copy-btn action-btn" data-keyword="${result.keyword}" title="Copy keyword">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn btn-sm favorite-btn action-btn ${isFavorite ? 'active' : ''}" 
                                data-keyword="${result.keyword}" title="Add to favorites">
                            <i class="fas fa-star"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tableHTML += '</tbody></table></div>';
        
        // Update results summary
        const summaryHTML = `
            <div class="row mb-3">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${results.length}</h5>
                            <p class="card-text">Keywords Analyzed</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${this.getHighOpportunityCount(results)}</h5>
                            <p class="card-text">High Opportunity</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${this.getAverageScore(results, 'difficulty_score').toFixed(1)}</h5>
                            <p class="card-text">Avg. Difficulty</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${this.getAverageScore(results, 'profitability_score').toFixed(1)}</h5>
                            <p class="card-text">Avg. Profitability</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        resultsContainer.innerHTML = summaryHTML + tableHTML;
        
        // Enable export buttons
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.disabled = false;
        });
    }
    
    getScoreColor(score, isReversed = false) {
        // For difficulty scores, lower is better (reversed)
        // For profitability scores, higher is better
        const adjustedScore = isReversed ? 100 - score : score;
        
        if (adjustedScore >= 70) return 'success';
        if (adjustedScore >= 50) return 'warning';
        if (adjustedScore >= 30) return 'info';
        return 'danger';
    }
    
    getHighOpportunityCount(results) {
        return results.filter(r => r.profitability_score >= 70).length;
    }
    
    getAverageScore(results, scoreType) {
        const scores = results.map(r => r[scoreType] || 0);
        return scores.reduce((a, b) => a + b, 0) / scores.length;
    }
    
    updateCharts(results) {
        this.createScoreChart(results);
        this.createVolumeChart(results);
    }
    
    createScoreChart(results) {
        const ctx = document.getElementById('scoreChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.scoreChart) {
            this.charts.scoreChart.destroy();
        }
        
        const data = {
            labels: results.slice(0, 10).map(r => r.keyword.substring(0, 20) + '...'),
            datasets: [{
                label: 'Difficulty Score',
                data: results.slice(0, 10).map(r => r.difficulty_score),
                backgroundColor: 'rgba(220, 53, 69, 0.8)',
                borderColor: 'rgb(220, 53, 69)',
                borderWidth: 1
            }, {
                label: 'Profitability Score',
                data: results.slice(0, 10).map(r => r.profitability_score),
                backgroundColor: 'rgba(40, 167, 69, 0.8)',
                borderColor: 'rgb(40, 167, 69)',
                borderWidth: 1
            }]
        };
        
        this.charts.scoreChart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Keyword Scores Comparison'
                    },
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }
    
    createVolumeChart(results) {
        const ctx = document.getElementById('volumeChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.volumeChart) {
            this.charts.volumeChart.destroy();
        }
        
        const data = {
            labels: results.slice(0, 10).map(r => r.keyword.substring(0, 20) + '...'),
            datasets: [{
                label: 'Search Volume',
                data: results.slice(0, 10).map(r => r.search_volume),
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 2,
                fill: false
            }]
        };
        
        this.charts.volumeChart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Search Volume Trend'
                    }
                }
            }
        });
    }
    
    async copyToClipboard(keyword) {
        try {
            await navigator.clipboard.writeText(keyword);
            this.showToast(`Copied "${keyword}" to clipboard`, 'success');
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = keyword;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showToast(`Copied "${keyword}" to clipboard`, 'success');
        }
    }
    
    async toggleFavorite(keyword, btn) {
        try {
            if (this.favorites.has(keyword)) {
                // Remove from favorites
                const response = await fetch('/remove_favorite', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ keyword })
                });
                
                const data = await response.json();
                if (data.success) {
                    this.favorites.delete(keyword);
                    btn.classList.remove('active');
                    this.showToast('Removed from favorites', 'info');
                }
            } else {
                // Add to favorites
                const keywordData = this.currentResults.find(r => r.keyword === keyword) || {};
                const response = await fetch('/add_favorite', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        keyword,
                        search_volume: keywordData.search_volume,
                        competition_score: keywordData.competition_score,
                        difficulty_score: keywordData.difficulty_score,
                        amazon_results: keywordData.amazon_results
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    this.favorites.add(keyword);
                    btn.classList.add('active');
                    this.showToast('Added to favorites', 'success');
                }
            }
        } catch (error) {
            console.error('Favorite toggle error:', error);
            this.showToast('Failed to update favorites', 'error');
        }
    }
    
    async loadFavorites() {
        try {
            // Load favorites from server or localStorage as fallback
            const saved = localStorage.getItem('kdp-favorites');
            if (saved) {
                this.favorites = new Set(JSON.parse(saved));
            }
        } catch (error) {
            console.error('Error loading favorites:', error);
        }
    }
    
    showSaveSessionForm() {
        if (!this.currentResults || this.currentResults.length === 0) {
            this.showToast('No data to save', 'warning');
            return;
        }
        
        const saveSessionForm = document.getElementById('saveSessionForm');
        const sessionNameInput = document.getElementById('sessionNameInput');
        
        if (saveSessionForm) {
            saveSessionForm.style.display = 'block';
            saveSessionForm.scrollIntoView({ behavior: 'smooth' });
            if (sessionNameInput) {
                sessionNameInput.focus();
                sessionNameInput.value = '';
            }
        }
    }
    
    hideSaveSessionForm() {
        const saveSessionForm = document.getElementById('saveSessionForm');
        if (saveSessionForm) {
            saveSessionForm.style.display = 'none';
        }
    }
    
    async saveSession() {
        const sessionNameInput = document.getElementById('sessionNameInput');
        if (!sessionNameInput) return;
        
        const sessionName = sessionNameInput.value.trim();
        if (!sessionName) {
            this.showToast('Please enter a session name', 'warning');
            sessionNameInput.focus();
            return;
        }
        
        try {
            const response = await fetch('/save_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_name: sessionName,
                    keywords_data: this.currentResults
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.showToast('Session saved successfully', 'success');
                this.hideSaveSessionForm();
            } else {
                this.showToast(data.error || 'Failed to save session', 'error');
            }
        } catch (error) {
            console.error('Save session error:', error);
            this.showToast('Failed to save session', 'error');
        }
    }
    
    async loadAutoSaveSession() {
        try {
            const response = await fetch('/load_session/0'); // 0 for autosave
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.keywords_data.length > 0) {
                    this.currentResults = data.keywords_data;
                    // Don't auto-display, just keep data available
                }
            }
        } catch (error) {
            console.error('Error loading autosave session:', error);
        }
    }
    
    async handleExport(e) {
        const format = e.target.dataset.format;
        
        if (!this.currentResults || this.currentResults.length === 0) {
            this.showToast('No data to export', 'warning');
            return;
        }
        
        try {
            this.setLoadingState(e.target, true);
            
            const response = await fetch(`/export/${format}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `keywords_export_${new Date().toISOString().slice(0, 10)}.${format}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showToast(`Export completed (${format.toUpperCase()})`, 'success');
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Export failed', 'error');
        } finally {
            this.setLoadingState(e.target, false);
        }
    }
    
    setupFilters() {
        // Implement filtering functionality if filter elements exist
        const filterInputs = document.querySelectorAll('.filter-input');
        filterInputs.forEach(input => {
            input.addEventListener('input', () => this.applyFilters());
        });
    }
    
    applyFilters() {
        // Filter the current results based on form inputs
        if (!this.currentResults) return;
        
        // This would filter the displayed results
        // Implementation depends on specific filter requirements
    }
    
    setLoadingState(element, isLoading) {
        if (isLoading) {
            element.disabled = true;
            element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        } else {
            element.disabled = false;
            element.innerHTML = element.dataset.originalText || 'Search';
        }
    }
    
    showToast(message, type = 'info') {
        // Create and show toast notification
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toastId = 'toast_' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.kdpTool = new KDPKeywordTool();
});

// Handle trending topic clicks
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('trending-topic-btn')) {
        const keyword = e.target.textContent.trim();
        const keywordsInput = document.getElementById('keywordsInput');
        if (keywordsInput) {
            keywordsInput.value = keyword;
            keywordsInput.focus();
        }
    }
});

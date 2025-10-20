// Osool Guide - Application Logic

// API Configuration
// Use relative URL to work on both localhost and HuggingFace
const API_BASE_URL = window.location.origin;

// DOM Elements
const queryInput = document.getElementById('queryInput');
const searchBtn = document.getElementById('searchBtn');
const loadingState = document.getElementById('loadingState');
const resultsContainer = document.getElementById('resultsContainer');
const errorContainer = document.getElementById('errorContainer');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');

// Language Toggle Elements
const btnEnglish = document.getElementById('btnEnglish');
const btnArabic = document.getElementById('btnArabic');

// Result Elements
const resultName = document.getElementById('resultName');
const nsgValue = document.getElementById('nsgValue');
const nscValue = document.getElementById('nscValue');
const incValue = document.getElementById('incValue');
const definitionText = document.getElementById('definitionText');
const reasoningText = document.getElementById('reasoningText');
const errorText = document.getElementById('errorText');

// Current language and cached data
let currentLanguage = 'en';
let cachedData = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkServerStatus();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    searchBtn.addEventListener('click', handleSearch);

    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent default newline behavior
            handleSearch();
        }
    });

    // Auto-resize textarea
    queryInput.addEventListener('input', () => {
        queryInput.style.height = 'auto';
        queryInput.style.height = queryInput.scrollHeight + 'px';
    });

    // Language toggle
    btnEnglish.addEventListener('click', () => switchLanguage('en'));
    btnArabic.addEventListener('click', () => switchLanguage('ar'));
}

// Switch Language
function switchLanguage(lang) {
    if (lang === currentLanguage) return;

    currentLanguage = lang;

    // Update button states
    if (lang === 'en') {
        btnEnglish.classList.add('active');
        btnArabic.classList.remove('active');
        document.body.classList.remove('rtl');
    } else {
        btnArabic.classList.add('active');
        btnEnglish.classList.remove('active');
        document.body.classList.add('rtl');
    }

    // Update displayed results if we have cached data
    if (cachedData) {
        updateResultsDisplay(cachedData);
    }
}

// Update Results Display Based on Current Language
function updateResultsDisplay(data) {
    // Name is ALWAYS in English (never translated)
    resultName.textContent = data.name || 'Unknown';

    if (currentLanguage === 'ar') {
        // Display Arabic for definition and reasoning only
        definitionText.textContent = data.definition_ar || data.definition || 'لا يوجد تعريف متاح.';
        reasoningText.textContent = data.reasoning_ar || data.reasoning || 'لا يوجد تفسير متاح.';
    } else {
        // Display English
        definitionText.textContent = data.definition || 'No definition available.';
        reasoningText.textContent = data.reasoning || 'No reasoning provided.';
    }

    // Codes are language-independent
    nsgValue.textContent = data.nsg || '--';
    nscValue.textContent = data.nsc_formatted || data.nsc || '--';
    incValue.textContent = data.inc || '--';
}

// Check Server Status
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            statusIndicator.className = 'status-online';
            statusText.textContent = `Online (${data.faiss_items.toLocaleString()} items)`;
        } else {
            statusIndicator.className = 'status-offline';
            statusText.textContent = 'Server Error';
        }
    } catch (error) {
        statusIndicator.className = 'status-offline';
        statusText.textContent = 'Server Offline';
    }
}

// Handle Search
async function handleSearch() {
    const query = queryInput.value.trim();

    if (!query) {
        showError('Please describe an asset to classify.');
        return;
    }

    // Show loading state
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/codify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            showError(data.error);
        } else {
            displayResults(data);
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to connect to the server. Please ensure the API is running.');
    }
}

// Display Results
function displayResults(data) {
    // Cache the data for language switching
    cachedData = data;

    // Hide loading and error
    loadingState.classList.add('hidden');
    errorContainer.classList.add('hidden');
    searchBtn.disabled = false;

    // Update display based on current language
    updateResultsDisplay(data);

    // Show results with animation
    resultsContainer.classList.remove('hidden');

    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Show Loading State
function showLoading() {
    resultsContainer.classList.add('hidden');
    errorContainer.classList.add('hidden');
    loadingState.classList.remove('hidden');
    searchBtn.disabled = true;
}

// Show Error
function showError(message) {
    loadingState.classList.add('hidden');
    resultsContainer.classList.add('hidden');
    errorText.textContent = message;
    errorContainer.classList.remove('hidden');
    searchBtn.disabled = false;
}

// Periodic status check (every 30 seconds)
setInterval(checkServerStatus, 30000);

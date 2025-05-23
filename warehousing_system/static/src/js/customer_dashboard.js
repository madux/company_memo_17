/** @odoo-module **/

// Public Warehouse Dashboard JavaScript
(function() {
    'use strict';

    /**
     * Warehouse Dashboard Controller
     * Plain JavaScript implementation for the combined template
     */
    class WarehouseDashboardController {
        constructor() {
            // Initialize state
            this.state = {
                filters: {
                    client: '',
                    month: 'All',
                    year: 'All'
                },
                isLoading: false,
                hasError: false,
                errorMessage: '',
                dashboardData: {},
                detailData: [],
                isDetailLoading: false
            };
            
            // DOM element references
            this.elements = {};
            this.detailModal = null;
            this.searchTimeout = null;
        }

        /**
         * Initialize the dashboard
         */
        async init() {
            console.log('Initializing Warehouse Dashboard...');
            
            // Get DOM element references
            this.cacheElementReferences();
            
            // Verify critical elements exist
            if (!this.elements.cardsContainer) {
                console.error('Cards container not found! Check if template loaded correctly.');
                return;
            }
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Setup modal
            this.setupModal();
            
            // Initial data fetch
            await this.fetchDashboardData();
            
            console.log('Dashboard initialized successfully');
        }

        /**
         * Cache references to DOM elements
         */
        cacheElementReferences() {
            this.elements = {
                clientFilter: document.getElementById('client-filter'),
                monthFilter: document.getElementById('month-filter'),
                yearFilter: document.getElementById('year-filter'),
                loadingState: document.getElementById('loading-state'),
                errorState: document.getElementById('error-state'),
                errorMessage: document.getElementById('error-message'),
                cardsContainer: document.getElementById('cards-container'),
                detailModal: document.getElementById('detailModal'),
                detailModalLabel: document.getElementById('detailModalLabel'),
                modalLoading: document.getElementById('modal-loading'),
                modalEmpty: document.getElementById('modal-empty'),
                modalTable: document.getElementById('modal-table'),
                detailTableBody: document.getElementById('detail-table-body')
            };

            // Log what we found
            console.log('Element references:', {
                cardsContainer: !!this.elements.cardsContainer,
                loadingState: !!this.elements.loadingState,
                errorState: !!this.elements.errorState
            });

            // Cache all card count elements
            const categories = [
                'waitingForInfo', 'expectedTomorrow', 'expectedToday', 'toBePutInStock',
                'withoutAllocatedStorage', 'labelsToBePrinted', 'longerThan90Days',
                'openOSDInventory', 'displacedItems', 'dispatchedItems'
            ];

            categories.forEach(category => {
                this.elements[`count-${category}`] = document.getElementById(`count-${category}`);
            });
        }

        /**
         * Set up event listeners
         */
        setupEventListeners() {
            // Filter event listeners
            if (this.elements.clientFilter) {
                this.elements.clientFilter.addEventListener('input', 
                    this.debounce(this.handleClientFilter.bind(this), 500)
                );
            }

            if (this.elements.monthFilter) {
                this.elements.monthFilter.addEventListener('change', 
                    this.handleMonthFilter.bind(this)
                );
            }

            if (this.elements.yearFilter) {
                this.elements.yearFilter.addEventListener('change', 
                    this.handleYearFilter.bind(this)
                );
            }

            // Card click event listeners
            document.querySelectorAll('.warehouse-card').forEach(card => {
                card.addEventListener('click', () => {
                    const category = card.getAttribute('data-category');
                    const title = card.getAttribute('data-title');
                    this.showDetailView(category, title);
                });
            });
        }

        /**
         * Setup Bootstrap modal
         */
        setupModal() {
            if (this.elements.detailModal) {
                if (window.bootstrap && window.bootstrap.Modal) {
                    this.detailModal = new window.bootstrap.Modal(this.elements.detailModal);
                } else if (window.$ && window.$.fn.modal) {
                    // Fallback for Bootstrap 4 with jQuery
                    this.detailModal = {
                        show: () => window.$('#detailModal').modal('show'),
                        hide: () => window.$('#detailModal').modal('hide')
                    };
                }
            }
        }

        /**
         * Handle client filter input
         */
        handleClientFilter(event) {
            this.state.filters.client = event.target.value;
            this.fetchDashboardData();
        }

        /**
         * Handle month filter change
         */
        handleMonthFilter(event) {
            this.state.filters.month = event.target.value;
            this.fetchDashboardData();
        }

        /**
         * Handle year filter change
         */
        handleYearFilter(event) {
            this.state.filters.year = event.target.value;
            this.fetchDashboardData();
        }

        /**
         * Update UI loading state
         */
        updateLoadingState(isLoading) {
            console.log('Updating loading state:', isLoading);
            this.state.isLoading = isLoading;
            
            if (this.elements.loadingState) {
                this.elements.loadingState.style.display = isLoading ? 'block' : 'none';
                console.log('Loading state display:', this.elements.loadingState.style.display);
            }
            
            if (this.elements.cardsContainer) {
                this.elements.cardsContainer.style.display = isLoading ? 'none' : 'block';
                console.log('Cards container display:', this.elements.cardsContainer.style.display);
            }
            
            if (this.elements.errorState) {
                this.elements.errorState.style.display = 'none';
            }
        }

        /**
         * Update UI error state
         */
        updateErrorState(hasError, errorMessage = '') {
            console.log('Updating error state:', hasError, errorMessage);
            this.state.hasError = hasError;
            this.state.errorMessage = errorMessage;
            
            if (this.elements.errorState) {
                this.elements.errorState.style.display = hasError ? 'block' : 'none';
            }
            
            if (this.elements.errorMessage && hasError) {
                this.elements.errorMessage.textContent = errorMessage;
            }
            
            if (this.elements.loadingState) {
                this.elements.loadingState.style.display = 'none';
            }
            
            if (this.elements.cardsContainer) {
                this.elements.cardsContainer.style.display = hasError ? 'none' : 'block';
            }
        }

        /**
         * Update dashboard card counts
         */
        updateCardCounts(data) {
            console.log('Updating card counts with data:', data);
            const categories = [
                'waitingForInfo', 'expectedTomorrow', 'expectedToday', 'toBePutInStock',
                'withoutAllocatedStorage', 'labelsToBePrinted', 'longerThan90Days',
                'openOSDInventory', 'displacedItems', 'dispatchedItems'
            ];

            categories.forEach(category => {
                const element = this.elements[`count-${category}`];
                if (element) {
                    const count = data[category] || 0;
                    element.textContent = count;
                    console.log(`Updated ${category}: ${count}`);
                } else {
                    console.warn(`Element not found for category: ${category}`);
                }
            });
        }

        /**
         * Fetch dashboard data from the server
         */
        async fetchDashboardData() {
            try {
                console.log('Starting data fetch...');
                this.updateLoadingState(true);
                this.updateErrorState(false);
                
                console.log('Fetching dashboard data with filters:', this.state.filters);
                
                const requestBody = {
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        client: this.state.filters.client,
                        month: this.state.filters.month,
                        year: this.state.filters.year
                    },
                    id: Math.floor(Math.random() * 1000000)
                };
                
                console.log('Request body:', requestBody);
                
                const response = await fetch('/warehouse/public/dashboard/data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
                });
                
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('Raw response data:', data);
                
                if (data.error) {
                    throw new Error(data.error.message || 'RPC Error');
                }
                
                console.log('Dashboard data received:', data.result);
                this.state.dashboardData = data.result || {};
                
                // Update the UI with new data
                this.updateCardCounts(this.state.dashboardData);
                
                // Force show cards container
                if (this.elements.cardsContainer) {
                    this.elements.cardsContainer.style.display = 'block';
                    console.log('Forced cards container to display: block');
                }
                
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
                this.updateErrorState(true, 'Failed to load dashboard data. Please try again later.');
            } finally {
                this.updateLoadingState(false);
            }
        }

        /**
         * Update modal loading state
         */
        updateModalLoadingState(isLoading) {
            if (this.elements.modalLoading) {
                this.elements.modalLoading.style.display = isLoading ? 'block' : 'none';
            }
            if (this.elements.modalEmpty) {
                this.elements.modalEmpty.style.display = 'none';
            }
            if (this.elements.modalTable) {
                this.elements.modalTable.style.display = 'none';
            }
        }

        /**
         * Update modal with detail data
         */
        updateModalContent(data) {
            if (!data || data.length === 0) {
                if (this.elements.modalEmpty) {
                    this.elements.modalEmpty.style.display = 'block';
                }
                return;
            }

            if (this.elements.modalTable && this.elements.detailTableBody) {
                // Clear existing content
                this.elements.detailTableBody.innerHTML = '';
                
                // Add new rows
                data.forEach(record => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${record.name || ''}</td>
                        <td>${record.client || ''}</td>
                        <td>${record.status || ''}</td>
                        <td>${record.scheduled_date || ''}</td>
                    `;
                    this.elements.detailTableBody.appendChild(row);
                });
                
                this.elements.modalTable.style.display = 'block';
            }
        }

        /**
         * Show detail view for the selected card
         */
        async showDetailView(cardId, title) {
            console.log('Showing detail view for:', cardId, title);
            
            // Update modal title
            if (this.elements.detailModalLabel) {
                this.elements.detailModalLabel.textContent = title;
            }
            
            // Show loading state
            this.updateModalLoadingState(true);
            
            // Show the modal
            if (this.detailModal && this.detailModal.show) {
                this.detailModal.show();
            }
            
            try {
                const response = await fetch('/warehouse/public/dashboard/action', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: {
                            cardSelected: cardId,
                            title: title,
                            client: this.state.filters.client,
                            month: this.state.filters.month,
                            year: this.state.filters.year
                        },
                        id: Math.floor(Math.random() * 1000000)
                    })
                });
                
                const data = await response.json();
                if (data.error) {
                    throw new Error(data.error.message || 'RPC Error');
                }
                
                console.log('Detail data received:', data.result);
                const detailData = Array.isArray(data.result) ? 
                    data.result : 
                    (data.result && data.result[0] ? data.result[0] : []);
                
                this.state.detailData = detailData;
                this.updateModalContent(detailData);
                
            } catch (error) {
                console.error('Error fetching detail data:', error);
                this.state.detailData = [];
                this.updateModalContent([]);
            } finally {
                this.updateModalLoadingState(false);
            }
        }

        /**
         * Utility function for debouncing
         */
        debounce(func, wait) {
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(this.searchTimeout);
                    func(...args);
                };
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(later, wait);
            }.bind(this);
        }
    }

    // Global dashboard instance
    let dashboardInstance = null;

    /**
     * Initialize the dashboard
     */
    function initWarehouseDashboard() {
        console.log('Initializing Warehouse Dashboard...');
        
        if (dashboardInstance) {
            console.log('Dashboard already initialized');
            return;
        }

        try {
            dashboardInstance = new WarehouseDashboardController();
            dashboardInstance.init();
            console.log('Dashboard initialized successfully');
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            
            // Show error in the dashboard container
            const dashboardEl = document.getElementById('public-warehouse-dashboard');
            if (dashboardEl) {
                dashboardEl.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fa fa-exclamation-triangle mr-2"></i>
                        Unable to load the dashboard: ${error.message}
                    </div>
                `;
            }
        }
    }

    // Make function globally available
    window.initWarehouseDashboard = initWarehouseDashboard;

    // Auto-initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, initializing dashboard...');
        
        // Add a small delay to ensure all elements are rendered
        setTimeout(() => {
            initWarehouseDashboard();
        }, 100);
    });

})();
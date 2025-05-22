/** @odoo-module **/

// Import OWL components properly for Odoo frontend
const { Component, useState, onMounted, onWillUnmount, mount } = owl;

/**
 * PublicWarehouseDashboard
 * 
 * Warehouse inventory dashboard component for public access
 */
class PublicWarehouseDashboard extends Component {
    static template = "warehousing_system.PublicWarehouseDashboardTemplate";

    setup() {
        // Initialize state
        this.state = useState({
            filters: {
                client: '',
                month: 'All',
                year: 'All'
            },
            detailViewCard: null,
            detailViewTitle: '',
            isLoading: true,
            hasError: false,
            errorMessage: '',
            dashboardData: {},
            detailData: [],
            isDetailLoading: false
        });
        
        // Reference to DOM elements we'll need
        this.detailModal = null;

        // Set up event listeners and fetch data on component mount
        onMounted(async () => {
            console.log('PublicWarehouseDashboard mounted');
            await this.setupFilterEvents();
            await this.fetchDashboardData();
            this.setupModal();
        });
        
        // Clean up on component unmount
        onWillUnmount(() => {
            this.cleanupFilterEvents();
        });
    }
    
    /**
     * Set up event listeners for filter inputs
     */
    async setupFilterEvents() {
        // Use setTimeout to ensure DOM is ready
        setTimeout(() => {
            this.clientInput = document.getElementById('client-filter');
            this.monthSelect = document.getElementById('month-filter');
            this.yearSelect = document.getElementById('year-filter');
            
            if (this.clientInput) {
                this.onClientInputHandler = this.handleClientInputDebounced.bind(this);
                this.clientInput.addEventListener('input', this.onClientInputHandler);
            }
            
            if (this.monthSelect) {
                this.onMonthChangeHandler = this.handleMonthChange.bind(this);
                this.monthSelect.addEventListener('change', this.onMonthChangeHandler);
            }
            
            if (this.yearSelect) {
                this.onYearChangeHandler = this.handleYearChange.bind(this);
                this.yearSelect.addEventListener('change', this.onYearChangeHandler);
            }
        }, 100);
    }

    /**
     * Setup Bootstrap modal
     */
    setupModal() {
        setTimeout(() => {
            const modalEl = document.getElementById('detailModal');
            if (modalEl) {
                if (window.bootstrap && window.bootstrap.Modal) {
                    this.detailModal = new window.bootstrap.Modal(modalEl);
                } else if (window.$ && window.$.fn.modal) {
                    // Fallback for Bootstrap 4 with jQuery
                    this.detailModal = {
                        show: () => window.$('#detailModal').modal('show'),
                        hide: () => window.$('#detailModal').modal('hide')
                    };
                }
            }
        }, 100);
    }
    
    /**
     * Clean up event listeners
     */
    cleanupFilterEvents() {
        if (this.clientInput && this.onClientInputHandler) {
            this.clientInput.removeEventListener('input', this.onClientInputHandler);
        }
        
        if (this.monthSelect && this.onMonthChangeHandler) {
            this.monthSelect.removeEventListener('change', this.onMonthChangeHandler);
        }
        
        if (this.yearSelect && this.onYearChangeHandler) {
            this.yearSelect.removeEventListener('change', this.onYearChangeHandler);
        }
        
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
    }
    
    /**
     * Handle client filter input with debouncing
     */
    handleClientInputDebounced(event) {
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        this.searchTimeout = setTimeout(() => {
            this.state.filters.client = event.target.value;
            this.fetchDashboardData();
        }, 500);
    }
    
    /**
     * Handle month filter change
     */
    handleMonthChange(event) {
        this.state.filters.month = event.target.value;
        this.fetchDashboardData();
    }
    
    /**
     * Handle year filter change
     */
    handleYearChange(event) {
        this.state.filters.year = event.target.value;
        this.fetchDashboardData();
    }
    
    /**
     * Fetch dashboard data from the server
     */
    async fetchDashboardData() {
        try {
            this.state.isLoading = true;
            this.state.hasError = false;
            
            console.log('Fetching dashboard data with filters:', this.state.filters);
            
            const response = await fetch('/warehouse/public/dashboard/data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
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
            
            console.log('Dashboard data received:', data.result);
            this.state.dashboardData = data.result || {};
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            this.state.hasError = true;
            this.state.errorMessage = 'Failed to load dashboard data. Please try again later.';
        } finally {
            this.state.isLoading = false;
        }
    }
    
    /**
     * Show detail view for the selected card
     */
    async showDetailView(cardId, title) {
        console.log('Showing detail view for:', cardId, title);
        
        this.state.detailViewCard = cardId;
        this.state.detailViewTitle = title;
        this.state.isDetailLoading = true;
        this.state.detailData = [];
        
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
            this.state.detailData = Array.isArray(data.result) ? data.result : (data.result && data.result[0] ? data.result[0] : []);
        } catch (error) {
            console.error('Error fetching detail data:', error);
            this.state.detailData = [];
        } finally {
            this.state.isDetailLoading = false;
        }
    }
}

// Initialize the component when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, checking for dashboard element...');
    
    const dashboardEl = document.getElementById('public-warehouse-dashboard');
    if (dashboardEl) {
        console.log('Dashboard element found, checking for OWL...');
        
        // Check if OWL is available
        if (typeof owl === 'undefined') {
            console.error('OWL framework not found');
            dashboardEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fa fa-exclamation-triangle mr-2"></i>
                    Unable to load the dashboard. OWL framework not available.
                </div>
            `;
            return;
        }
        
        console.log('OWL found, mounting component...');
        
        try {
            // Use OWL's mount function properly
            const app = mount(PublicWarehouseDashboard, dashboardEl, { 
                env: {}, 
                dev: true 
            });
            console.log('Dashboard component mounted successfully');
        } catch (error) {
            console.error("Error initializing dashboard:", error);
            dashboardEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fa fa-exclamation-triangle mr-2"></i>
                    Unable to load the dashboard: ${error.message}
                </div>
            `;
        }
    } else {
        console.log('Dashboard element not found, will try again in 1 second...');
        // Try again after a delay
        setTimeout(() => {
            const dashboardEl2 = document.getElementById('public-warehouse-dashboard');
            if (dashboardEl2) {
                try {
                    const app = mount(PublicWarehouseDashboard, dashboardEl2, { 
                        env: {}, 
                        dev: true 
                    });
                    console.log('Dashboard component mounted successfully (delayed)');
                } catch (error) {
                    console.error("Error initializing dashboard (delayed):", error);
                    dashboardEl2.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fa fa-exclamation-triangle mr-2"></i>
                            Unable to load the dashboard: ${error.message}
                        </div>
                    `;
                }
            }
        }, 1000);
    }
});
/** @odoo-module **/

// Alternative approach with inline template - Fixed loading issue
(function() {
    'use strict';

    // Check if OWL is available
    if (typeof owl === 'undefined') {
        console.error('OWL framework not found');
        return;
    }

    // Import OWL components
    const { Component, useState, onMounted, onWillUnmount, mount, xml } = owl;

    // Define template inline
    const TEMPLATE = xml`
        <div>
            <!-- Filters -->
            <div class="dashboard-filters mb-4">
                <div class="row">
                    <div class="col-md-4">
                        <label>Client</label>
                        <input type="text" class="form-control" id="client-filter"
                               placeholder="Search by client name" t-att-value="state.filters.client"/>
                    </div>
                    <div class="col-md-4">
                        <label>Month</label>
                        <select class="form-control" id="month-filter" t-att-value="state.filters.month">
                            <option value="All">All</option>
                            <option value="Jan">Jan</option>
                            <option value="Feb">Feb</option>
                            <option value="Mar">Mar</option>
                            <option value="Apr">Apr</option>
                            <option value="May">May</option>
                            <option value="Jun">Jun</option>
                            <option value="Jul">Jul</option>
                            <option value="Aug">Aug</option>
                            <option value="Sep">Sep</option>
                            <option value="Oct">Oct</option>
                            <option value="Nov">Nov</option>
                            <option value="Dec">Dec</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label>Year</label>
                        <select class="form-control" id="year-filter" t-att-value="state.filters.year">
                            <option value="All">All</option>
                            <option value="2025">2025</option>
                            <option value="2024">2024</option>
                            <option value="2023">2023</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Dashboard Cards -->
            <div id="dashboard-cards" class="dashboard-cards">
                <!-- Loading state -->
                <div t-if="state.isLoading" class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <p class="mt-2">Loading dashboard data...</p>
                </div>
                
                <!-- Error state -->
                <div t-elif="state.hasError" class="alert alert-danger" role="alert">
                    <i class="fa fa-exclamation-triangle mr-2"></i> <t t-esc="state.errorMessage"/>
                </div>
                
                <!-- Dashboard cards - Only show when not loading and no error -->
                <div t-elif="!state.isLoading and !state.hasError" class="row">
                    <!-- Waiting For Info -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('waitingForInfo', 'Inventory Items Waiting for Info')">
                            <div class="card-icon"><i class="fa fa-info-circle"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.waitingForInfo || 0"/></div>
                            <div class="card-title">Inventory Items Waiting for Info</div>
                        </div>
                    </div>
                    
                    <!-- Expected Tomorrow -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('expectedTomorrow', 'Inventory Items Expected Tomorrow')">
                            <div class="card-icon"><i class="fa fa-hourglass-half"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.expectedTomorrow || 0"/></div>
                            <div class="card-title">Inventory Items Expected Tomorrow</div>
                        </div>
                    </div>
                    
                    <!-- Expected Today -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('expectedToday', 'Inventory Items Expected Today')">
                            <div class="card-icon"><i class="fa fa-clock-o"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.expectedToday || 0"/></div>
                            <div class="card-title">Inventory Items Expected Today</div>
                        </div>
                    </div>
                    
                    <!-- To Be Put In Stock -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('toBePutInStock', 'Items to be Put in Stock')">
                            <div class="card-icon"><i class="fa fa-cart-plus"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.toBePutInStock || 0"/></div>
                            <div class="card-title">Items to be Put in Stock</div>
                        </div>
                    </div>
                    
                    <!-- Without Allocated Storage -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('withoutAllocatedStorage', 'Inventory Items without Allocated Storage')">
                            <div class="card-icon"><i class="fa fa-ban"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.withoutAllocatedStorage || 0"/></div>
                            <div class="card-title">Inventory Items without Allocated Storage</div>
                        </div>
                    </div>
                    
                    <!-- Labels To Be Printed -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('labelsToBePrinted', 'Labels to be Printed')">
                            <div class="card-icon"><i class="fa fa-print"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.labelsToBePrinted || 0"/></div>
                            <div class="card-title">Labels to be Printed</div>
                        </div>
                    </div>
                    
                    <!-- Longer Than 90 Days -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('longerThan90Days', 'Inventory Items >90 Days in Stock')">
                            <div class="card-icon"><i class="fa fa-clock"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.longerThan90Days || 0"/></div>
                            <div class="card-title">Inventory Items >90 Days in Stock</div>
                        </div>
                    </div>
                    
                    <!-- Open OSD Inventory -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('openOSDInventory', 'Open OS&amp;D Inventory in Stock')">
                            <div class="card-icon"><i class="fa fa-unlock-alt"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.openOSDInventory || 0"/></div>
                            <div class="card-title">Open OS&amp;D Inventory in Stock</div>
                        </div>
                    </div>
                    
                    <!-- Displaced Items -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('displacedItems', 'Inventory Items Displaced')">
                            <div class="card-icon"><i class="fa fa-truck-moving"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.displacedItems || 0"/></div>
                            <div class="card-title">Inventory Items Displaced</div>
                        </div>
                    </div>
                    
                    <!-- Dispatched Items -->
                    <div class="col-md-4 col-lg-3 mb-4">
                        <div class="warehouse-card red-card" t-on-click="() => this.showDetailView('dispatchedItems', 'Inventory Items Dispatched')">
                            <div class="card-icon"><i class="fa fa-truck"></i></div>
                            <div class="card-count"><t t-esc="state.dashboardData.dispatchedItems || 0"/></div>
                            <div class="card-title">Inventory Items Dispatched</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Detail Modal -->
            <div class="modal fade" id="detailModal" tabindex="-1" role="dialog"
                 aria-labelledby="detailModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="detailModalLabel"><t t-esc="state.detailViewTitle"/></h5>
                            <button type="button" class="close" data-dismiss="modal"
                                    aria-label="Close"><span aria-hidden="true">×</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <!-- Loading state -->
                            <div t-if="state.isDetailLoading" class="text-center py-4">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="sr-only">Loading...</span>
                                </div>
                                <p class="mt-2">Loading details...</p>
                            </div>
                            
                            <!-- Empty state -->
                            <div t-elif="!state.isDetailLoading and state.detailData.length === 0" class="alert alert-info" role="alert">
                                <i class="fa fa-info-circle mr-2"></i> No items found for this category.
                            </div>
                            
                            <!-- Detail table -->
                            <div t-elif="!state.isDetailLoading and state.detailData.length > 0" class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Reference</th>
                                            <th>Client</th>
                                            <th>Status</th>
                                            <th>Scheduled Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr t-foreach="state.detailData" t-as="record" t-key="record.id">
                                            <td><t t-esc="record.name || ''"/></td>
                                            <td><t t-esc="record.client || ''"/></td>
                                            <td><t t-esc="record.status || ''"/></td>
                                            <td><t t-esc="record.scheduled_date || ''"/></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    /**
     * PublicWarehouseDashboard
     * 
     * Warehouse inventory dashboard component for public access
     */
    class PublicWarehouseDashboard extends Component {
        static template = TEMPLATE;

        setup() {
            // Initialize state - START WITH LOADING FALSE
            this.state = useState({
                filters: {
                    client: '',
                    month: 'All',
                    year: 'All'
                },
                detailViewCard: null,
                detailViewTitle: '',
                isLoading: false,  // Changed to false initially
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
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                if (data.error) {
                    throw new Error(data.error.message || 'RPC Error');
                }
                
                console.log('Dashboard data received:', data.result);
                this.state.dashboardData = data.result || {};
                
                // Force a small delay to ensure state update is processed
                await new Promise(resolve => setTimeout(resolve, 50));
                
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
                this.state.hasError = true;
                this.state.errorMessage = 'Failed to load dashboard data. Please try again later.';
            } finally {
                // Ensure loading is always set to false
                this.state.isLoading = false;
                console.log('Loading state set to false, dashboardData:', this.state.dashboardData);
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

    // Function to initialize the dashboard
    function initializeDashboard() {
        console.log('Initializing dashboard with inline template...');
        
        const dashboardEl = document.getElementById('public-warehouse-dashboard');
        if (!dashboardEl) {
            console.log('Dashboard element not found');
            return false;
        }

        console.log('Dashboard element found, mounting component...');
        
        try {
            // Mount the component
            const app = mount(PublicWarehouseDashboard, dashboardEl, { 
                env: {}, 
                dev: false
            });
            console.log('Dashboard component mounted successfully');
            return true;
        } catch (error) {
            console.error("Error initializing dashboard:", error);
            dashboardEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fa fa-exclamation-triangle mr-2"></i>
                    Unable to load the dashboard: ${error.message}
                </div>
            `;
            return false;
        }
    }

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, initializing dashboard with inline template...');
        
        // Try immediate initialization
        if (!initializeDashboard()) {
            // If that fails, wait a bit and try again
            setTimeout(function() {
                console.log('Retrying dashboard initialization...');
                initializeDashboard();
            }, 1000);
        }
    });

})();
/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * PublicWarehouseDashboard
 * 
 * Warehouse inventory dashboard component for public access
 */
export class PublicWarehouseDashboard extends Component {
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

        // Get HTTP service for API calls
        this.http = useService("http");
        
        // Reference to DOM elements we'll need
        this.detailModal = null;

        // Set up event listeners and fetch data on component mount
        onMounted(() => {
            this.setupFilterEvents();
            this.fetchDashboardData();
            
            // Store reference to Bootstrap modal
            this.detailModal = new bootstrap.Modal(document.getElementById('detailModal'));
        });
        
        // Clean up on component unmount
        onWillUnmount(() => {
            this.cleanupFilterEvents();
        });
    }
    
    /**
     * Set up event listeners for filter inputs
     */
    setupFilterEvents() {
        // Client filter with debounce
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
            
            const result = await this.http.post('/warehouse/public/dashboard/data', {
                client: this.state.filters.client,
                month: this.state.filters.month,
                year: this.state.filters.year
            });
            
            this.state.dashboardData = result;
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
        this.state.detailViewCard = cardId;
        this.state.detailViewTitle = title;
        this.state.isDetailLoading = true;
        this.state.detailData = [];
        
        // Show the modal
        this.detailModal.show();
        
        try {
            const result = await this.http.post('/warehouse/public/dashboard/action', {
                cardSelected: cardId,
                title: title,
                client: this.state.filters.client,
                month: this.state.filters.month,
                year: this.state.filters.year
            });
            
            this.state.detailData = result;
        } catch (error) {
            console.error('Error fetching detail data:', error);
            this.state.detailData = [];
        } finally {
            this.state.isDetailLoading = false;
        }
    }
}

// Define the component's template
PublicWarehouseDashboard.template = 'warehousing_system.PublicWarehouseDashboardTemplate';

// Register the component to be mounted
// This component will be mounted by the web_component_loader controller
document.addEventListener('DOMContentLoaded', () => {
    const dashboardEl = document.getElementById('public-warehouse-dashboard');
    if (dashboardEl) {
        const env = owl.Component.env;
        const app = new PublicWarehouseDashboard();
        app.mount(dashboardEl, { env });
    }
});
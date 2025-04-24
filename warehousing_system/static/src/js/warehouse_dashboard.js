/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

class WarehouseDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        // Remove notification service reference since it's not available or defined differently
        
        // Initialize state with default values
        this.state = useState({
            filters: {
                client: '',  // Empty string for text input
                fileType: 'All',
                projectNo: 'All',
                month: 'All',
                year: 'All'
            },
            statusOptions: [
                { id: 'All', name: 'All' },
                { id: 'draft', name: 'Draft' },
                { id: 'arrived', name: 'Arrived at Warehouse' },
                { id: 'allocated', name: 'Allocated' },
                { id: 'waiting', name: 'Waiting' },
                { id: 'done', name: 'Processed / Shipped' },
                { id: 'cancelled', name: 'Cancelled' }
            ],
            projectOptions: [{ id: 'All', name: 'All' }],
            stats: {
                waitingForInfo: 0,
                expectedTomorrow: 0,
                expectedToday: 0,
                toBePutInStock: 0,
                withoutAllocatedStorage: 0,
                labelsToBePrinted: 0,
                longerThan90Days: 0,
                openOSDInventory: 0,
                displachedItems: 0,
                dispatchedItems: 0
            }
        });

        onWillStart(async () => {
            await this.loadFilterOptions();
            await this.fetchDashboardData();
        });
    }

    async loadFilterOptions() {
        try {
            // Load project numbers (from unique supplier_po_number values)
            const projects = await this.orm.call(
                'stock.picking',
                'search_read',
                [[['supplier_po_number', '!=', false]]],
                { fields: ['supplier_po_number'] }
            );
            
            // Get unique project numbers
            const uniqueProjects = [...new Set(projects.map(p => p.supplier_po_number))];
            this.state.projectOptions = [
                { id: 'All', name: 'All' },
                ...uniqueProjects.map(p => ({ id: p, name: p }))
            ];
        } catch (error) {
            console.error("Failed to load filter options:", error);
            // Remove notification code
        }
    }

    async fetchDashboardData() {
        try {
            // Prepare filter data for backend
            const filterData = {
                client: this.state.filters.client,
                fileType: this.state.filters.fileType,
                projectNo: this.state.filters.projectNo,
                month: this.state.filters.month,
                year: this.state.filters.year
            };
            
            // Fetch all stats in a single call for better performance
            const stats = await this.orm.call(
                'stock.picking',
                'get_warehouse_dashboard_data',
                [filterData]
            );
           
            // Update state with fetched data
            this.state.stats = stats || {
                waitingForInfo: 0,
                expectedTomorrow: 0,
                expectedToday: 0,
                toBePutInStock: 0,
                withoutAllocatedStorage: 0,
                labelsToBePrinted: 0,
                longerThan90Days: 0,
                openOSDInventory: 0,
                displachedItems: 0,
                dispatchedItems: 0
            };
        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
            // Remove notification code
        }
    }

    onFilterChange(event, filterName) {
        this.state.filters[filterName] = event.target.value;
        this.fetchDashboardData();
    }

    // For text input we need a separate handler with debounce
    onClientInputChange(event) {
        this.state.filters.client = event.target.value;
        this._debouncedFetch();
    }

    // Simple debounce implementation to avoid too many API calls while typing
    _debouncedFetch() {
        if (this._searchTimeout) {
            clearTimeout(this._searchTimeout);
        }
        this._searchTimeout = setTimeout(() => {
            this.fetchDashboardData();
        }, 500);
    }

    // Helper method to generate domain for card clicks based on current filters
    getDomainWithFilters(additionalDomain = []) {
        let domain = [...additionalDomain];
        
        // Add client filter (customer_id.name) if not empty
        if (this.state.filters.client && this.state.filters.client.trim() !== '') {
            domain.push(['customer_id.name', 'ilike', this.state.filters.client.trim()]);
        }
        
        // Add file type filter (inventory_status)
        if (this.state.filters.fileType !== 'All') {
            domain.push(['inventory_status', '=', this.state.filters.fileType]);
        }
        
        // Add project number filter (supplier_po_number)
        if (this.state.filters.projectNo !== 'All') {
            domain.push(['supplier_po_number', '=', this.state.filters.projectNo]);
        }
        
        // Add date filters (month and year)
        if (this.state.filters.month !== 'All' || this.state.filters.year !== 'All') {
            const monthMapping = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            };
            
            let year = this.state.filters.year === 'All' ? new Date().getFullYear() : parseInt(this.state.filters.year);
            
            if (this.state.filters.month !== 'All') {
                const monthNum = monthMapping[this.state.filters.month];
                const startDate = `${year}-${monthNum.toString().padStart(2, '0')}-01`;
                
                let endMonth = monthNum === 12 ? 1 : monthNum + 1;
                let endYear = monthNum === 12 ? year + 1 : year;
                const endDate = `${endYear}-${endMonth.toString().padStart(2, '0')}-01`;
                
                domain.push(['create_date', '>=', startDate]);
                domain.push(['create_date', '<', endDate]);
            } else if (this.state.filters.year !== 'All') {
                domain.push(['create_date', '>=', `${year}-01-01`]);
                domain.push(['create_date', '<', `${year+1}-01-01`]);
            }
        }
        
        return domain;
    }

    async onCardClick(actionName, domainAddition, title) {
        try {
            // Combine card-specific domain with filter domain
            const domain = this.getDomainWithFilters(domainAddition);
            
            await this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'tree,form',
                domain: domain,
                name: title,
                context: {
                    // Include current filters in context
                    search_default_client: this.state.filters.client || false,
                    search_default_fileType: this.state.filters.fileType !== 'All' ? this.state.filters.fileType : false,
                    search_default_projectNo: this.state.filters.projectNo !== 'All' ? this.state.filters.projectNo : false,
                    search_default_month: this.state.filters.month !== 'All' ? this.state.filters.month : false,
                    search_default_year: this.state.filters.year !== 'All' ? this.state.filters.year : false
                }
            });
        } catch (error) {
            console.error("Failed to execute action:", error);
            // Remove notification code
        }
    }
}

WarehouseDashboard.template = 'warehousing_system.WarehouseDashboard';
WarehouseDashboard.props = {};

registry.category("actions").add("warehouse_inventory_dashboard", WarehouseDashboard);

export default WarehouseDashboard;
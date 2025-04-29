/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState, onMounted } from "@odoo/owl";

class WarehouseDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        
        this.state = useState({
            filters: {
                client: '',
                fileType: 'All',
                projectNo: '',
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
            await this.fetchDashboardData();
        });
        
        onMounted(() => {
            // Ensure proper layout rendering after component is mounted
            this._adjustLayout();
            
            // Add resize listener for responsive adjustments
            window.addEventListener('resize', this._adjustLayout);
        });
    }
    
    _adjustLayout() {
        // Force recalculation of layout after render
        const dashboard = document.querySelector('.warehouse-dashboard');
        if (dashboard) {
            // Trigger browser reflow
            void dashboard.offsetWidth;
        }
    }
    
    async fetchDashboardData() {
        try {
            const filterData = {
                client: this.state.filters.client,
                fileType: this.state.filters.fileType,
                projectNo: this.state.filters.projectNo,
                month: this.state.filters.month,
                year: this.state.filters.year
            };
            
            const stats = await this.orm.call(
                'stock.picking',
                'get_warehouse_dashboard_data',
                [filterData]
            );
           
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
        }
    }
    
    onFilterChange(event, filterName) {
        this.state.filters[filterName] = event.target.value;
        this.fetchDashboardData();
    }

    onClientInputChange(event, filterName) {
        this.state.filters[filterName] = event.target.value;
        this._debouncedFetch();
    }

    _debouncedFetch() {
        if (this._searchTimeout) {
            clearTimeout(this._searchTimeout);
        }
        this._searchTimeout = setTimeout(() => {
            this.fetchDashboardData();
        }, 500);
    }

    getDomainWithFilters(additionalDomain = []) {
        let domain = [...additionalDomain];
        
        if (this.state.filters.client && this.state.filters.client.trim() !== '') {
            domain.push(['customer_id.name', 'ilike', this.state.filters.client.trim()]);
        }
        
        if (this.state.filters.fileType !== 'All') {
            domain.push(['inventory_status', '=', this.state.filters.fileType]);
        }
        
        if (this.state.filters.projectNo && this.state.filters.projectNo.trim() !== '') {
            domain.push(['supplier_po_number', 'ilike', this.state.filters.projectNo.trim()]);
        }
        
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
            const domain = this.getDomainWithFilters(domainAddition);
            await this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'tree,form',
                domain: domain,
                name: title,
                context: {
                    search_default_client: this.state.filters.client || false,
                    search_default_fileType: this.state.filters.fileType !== 'All' ? this.state.filters.fileType : false,
                    search_default_projectNo: this.state.filters.projectNo || false,
                    search_default_month: this.state.filters.month !== 'All' ? this.state.filters.month : false,
                    search_default_year: this.state.filters.year !== 'All' ? this.state.filters.year : false
                }
            });
        } catch (error) {
            console.error("Failed to execute action:", error);
            // Use the correct notification method - add instead of notify
            this.notificationService.add(
                "Failed to open view. Please try again.",
                {
                    type: "warning",
                    title: "Action Error",
                }
            );
        }
    }
    
    // Clean up method to remove event listener
    willUnmount() {
        window.removeEventListener('resize', this._adjustLayout);
    }
}

WarehouseDashboard.template = 'warehousing_system.WarehouseDashboard';
WarehouseDashboard.props = {};

registry.category("actions").add("warehouse_inventory_dashboard", WarehouseDashboard);

export default WarehouseDashboard;
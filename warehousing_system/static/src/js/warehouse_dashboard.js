/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState, onMounted } from "@odoo/owl";

class WarehouseDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notificationService = useService("notification");
        
        this.state = useState({
            filters: {
                client: 'Saipem',
                fileType: 'Warehouse',
                projectNo: 'PR02345',
                month: 'Jan',
                year: 'All'
            },
            stats: {
                waitingForInfo: 0,
                expectedTomorrow: 0,
                expectedToday: 0,
                toBePutInStock: 0,
                withoutAllocatedStorage: 0,
                labelsToBePrinted: 0,
                longerThan90Days: 0,
                openOSDInventory: 0,
                displachedItems: 0
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
            // Fetch all stats in a single call for better performance
            const stats = await this.orm.call(
                'stock.picking',
                'get_warehouse_dashboard_data',
                [this.state.filters]  // Pass filters to the backend
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
                displachedItems: 0
            };
        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
            // Use the correct notification method - add instead of notify
            this.notificationService.add(
                "Failed to load dashboard data. Please try again later.",
                {
                    type: "danger",
                    title: "Dashboard Error",
                }
            );
        }
    }
    
    onFilterChange(event, filterName) {
        this.state.filters[filterName] = event.target.value;
        this.fetchDashboardData();
    }
    
    async onCardClick(actionName, domain, title) {
        try {
            await this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'tree,form',
                domain: domain,
                name: title,
                context: {
                    ...this.state.filters  // Include current filters in context
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
/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState, onMounted } from "@odoo/owl";

class WarehouseDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        this.notificationService = useService("notification");
        
        this.state = useState({
            filters: {
                client: '',
                // fileType: 'warehouse',
                // projectNo: '',
                month: 'All',
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
                displacedItems: 0,
                dispatchedItems: 0
            }
        });
        
        onWillStart(async () => {
            await this.fetchDashboardData();
        });
        
    }
    
    
    async fetchDashboardData() {
        try {
            const filterData = {
                client: this.state.filters.client,
                // fileType: this.state.filters.fileType,
                // projectNo: this.state.filters.projectNo,
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
                displacedItems: 0,
                dispatchedItems: 0
            };
            
        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
            this.notificationService.add(
                "Failed to fetch dashboard data. Please try again.",
                {
                    type: "warning",
                    title: "Dashboard Error",
                }
            );
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

    async onCardClick(actionName, cardSelected, title) {
        try {

            const filterData = {
                client: this.state.filters.client,
                month: this.state.filters.month,
                year: this.state.filters.year
            };
                        
            const actionData = {
                title: title,
                cardSelected: cardSelected || {},
                filterData
            };

            const result = await this.orm.call(
                'stock.picking',
                'get_action',
                [actionData]
            );

            if (result && result.action) {
                await this.actionService.doAction(result.action);
            }
        } catch (error) {
            console.error("Failed to execute action:", error);
            this.notificationService.add(
                "Failed to open view. Please try again.",
                {
                    type: "warning",
                    title: "Action Error",
                }
            );
        }
    }
    
    willUnmount() {
        window.removeEventListener('resize', this._adjustLayout);
    }
}

WarehouseDashboard.template = 'warehousing_system.WarehouseDashboard';

WarehouseDashboard.props = {};

registry.category("actions").add("warehouse_inventory_dashboard", WarehouseDashboard);

export default WarehouseDashboard;
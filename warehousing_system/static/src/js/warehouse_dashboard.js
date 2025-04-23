/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

class WarehouseDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
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
    }

    async fetchDashboardData() {
        try {
            // Fetch all stats in a single call for better performance
            const stats = await this.orm.call(
                'stock.picking',
                'get_warehouse_dashboard_data',
                []
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
        }
    }

    onFilterChange(event, filterName) {
        this.state.filters[filterName] = event.target.value;
        this.fetchDashboardData();
    }

    async onCardClick(actionName, domain, title) {
        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_mode: 'tree,form',
            domain: domain,
            name: title,
        });
    }
}

WarehouseDashboard.template = 'warehousing_system.WarehouseDashboard';
WarehouseDashboard.props = {};

registry.category("actions").add("warehouse_inventory_dashboard", WarehouseDashboard);

export default WarehouseDashboard;
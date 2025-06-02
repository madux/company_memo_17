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
                fileType: '',
                projectNo: '',
                month: '',
                year: ''
            },
            statusOptions: [
                { id: 'warehouse', name: 'WAREHOUSING' },
                { id: 'transport', name: 'TRANSPORT' },
                { id: 'travel', name: 'TRAVEL' },
                { id: 'agency', name: 'AGENCY' },
                { id: 'cfwd', name: 'CFWD' },
                { id: 'procurement', name: 'PROCUREMENT'}
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

    getDomainWithFilters(additionalDomain = []) {
        let domain = [...additionalDomain];
        
        // 
        
        if (this.state.filters.fileType === 'warehouse') {
            if (this.state.filters.projectNo && this.state.filters.projectNo.trim() !== '') {
                domain.push(['origin', 'ilike', this.state.filters.projectNo.trim()]);
            }

            if (this.state.filters.client && this.state.filters.client.trim() !== '') {
                domain.push(['customer_id.name', 'ilike', this.state.filters.client.trim()]);
            }
        }
        
        // if (this.state.filters.projectNo && this.state.filters.projectNo.trim() !== '') {
        //     domain.push(['supplier_po_number', 'ilike', this.state.filters.projectNo.trim()]);
        // }
        else {
            domain.push(['memo_project_type', '=', this.state.filters.fileType]);
            if (this.state.filters.projectNo && this.state.filters.projectNo.trim() !== '') {
                domain.push(['code', 'ilike', this.state.filters.projectNo.trim()]);
            }

            if (this.state.filters.client && this.state.filters.client.trim() !== '') {
                domain.push(['client_id.name', 'ilike', this.state.filters.client.trim()]);
            }
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

    async onCardClick(actionName, cardDomain, cardContext, title) {
        try {
            // const domain = this.getDomainWithFilters(domainAddition);
            // await this.actionService.doAction({
            //     type: 'ir.actions.act_window',
            //     res_model: 'stock.picking',
            //     view_mode: 'tree,form',
            const domain = this.getDomainWithFilters(cardDomain);
            const context = cardContext || {};
            // const context = cardFlag ? { [cardFlag]: true } : {};

            console.log('Domain:', domain);
            console.log('Context:', context);

            const actionData = {
                title: title,
                domain: domain,
                // name: title,
                // context: {
                //     search_default_client: this.state.filters.client || false,
                //     search_default_fileType: this.state.filters.fileType !== 'All' ? this.state.filters.fileType : false,
                //     search_default_projectNo: this.state.filters.projectNo || false,
                //     search_default_month: this.state.filters.month !== 'All' ? this.state.filters.month : false,
                //     search_default_year: this.state.filters.year !== 'All' ? this.state.filters.year : false
                // }
                context: context
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
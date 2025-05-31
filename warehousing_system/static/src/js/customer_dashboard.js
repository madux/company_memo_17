/** @odoo-module **/

// Customer Warehouse Dashboard JavaScript
(function() {
    'use strict';

    class WarehouseDashboardController {
        constructor() {
            this.state = {
                filters: { client: '', month: 'All', year: 'All' },
                isLoading: false,
                hasError: false,
                dashboardData: {}
            };
            this.elements = {};
            this.searchTimeout = null;
        }

        async init() {
            this.cacheElementReferences();
            if (!this.elements.cardsContainer) {
                console.error('Cards container missing!');
                return;
            }
            this.setupEventListeners();
            this.setupModal();
            await this.fetchDashboardData();
        }

        cacheElementReferences() {
            this.elements = {
                clientFilter: document.getElementById('client-filter'),
                monthFilter:  document.getElementById('month-filter'),
                yearFilter:   document.getElementById('year-filter'),
                loadingState: document.getElementById('loading-state'),
                errorState:   document.getElementById('error-state'),
                errorMessage: document.getElementById('error-message'),
                cardsContainer: document.getElementById('cards-container'),
                detailModal: document.getElementById('detailModal'),
                detailModalLabel: document.getElementById('detailModalLabel'),
                modalLoading: document.getElementById('modal-loading'),
                modalEmpty: document.getElementById('modal-empty'),
                modalTable: document.getElementById('modal-table'),
                detailTableBody: document.getElementById('detail-table-body')
            };
            // map counts
            ['waitingForInfo','expectedTomorrow','expectedToday','toBePutInStock',
             'withoutAllocatedStorage','labelsToBePrinted','longerThan90Days',
             'openOSDInventory','displacedItems','dispatchedItems'
            ].forEach(cat => {
                this.elements[`count-${cat}`] = document.getElementById(`count-${cat}`);
            });
        }

        setupEventListeners() {
            if (this.elements.clientFilter)
                this.elements.clientFilter.addEventListener('input',
                    this.debounce(ev => this.onFilterChange(ev, 'client'), 500)
                );
            if (this.elements.monthFilter)
                this.elements.monthFilter.addEventListener('change',
                    ev => this.onFilterChange(ev, 'month')
                );
            if (this.elements.yearFilter)
                this.elements.yearFilter.addEventListener('change',
                    ev => this.onFilterChange(ev, 'year')
                );

            document.querySelectorAll('.warehouse-card').forEach(card => {
                card.addEventListener('click', () => {
                    this.onCardClick(
                        card.dataset.category,
                        card.dataset.title
                    );
                });
            });
        }

        onFilterChange(ev, field) {
            this.state.filters[field] = ev.target.value;
            this.fetchDashboardData();
        }

        setupModal() {
            if (this.elements.detailModal && window.bootstrap?.Modal) {
                this.detailModal = new window.bootstrap.Modal(this.elements.detailModal);
            }
        }

        updateLoadingState(isLoading) {
            this.state.isLoading = isLoading;
            if (this.elements.loadingState) {
                this.elements.loadingState.style.display = isLoading ? '' : 'none';
            }
            // instead of setting block/flex, just hide: when not loading, clear any inline;
            if (this.elements.cardsContainer) {
                if (isLoading) {
                    this.elements.cardsContainer.style.display = 'none';
                } else {
                    this.elements.cardsContainer.style.removeProperty('display');
                }
            }
            if (this.elements.errorState) {
                this.elements.errorState.style.display = 'none';
            }
        }

        updateErrorState(hasError, msg='') {
            this.state.hasError = hasError;
            if (this.elements.errorState) {
                this.elements.errorState.style.display = hasError ? '' : 'none';
            }
            if (this.elements.errorMessage) {
                this.elements.errorMessage.textContent = msg;
            }
            // hide loading
            if (this.elements.loadingState) {
                this.elements.loadingState.style.display = 'none';
            }
        }

        updateCardCounts(data) {
            Object.entries(data).forEach(([key,value]) => {
                const el = this.elements[`count-${key}`];
                if (el) el.textContent = value || 0;
            });
        }

        async fetchDashboardData() {
            try {
                this.updateLoadingState(true);
                this.updateErrorState(false);
                const res = await fetch('/warehouse/public/dashboard/data', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({
                        jsonrpc: '2.0', method: 'call',
                        params: this.state.filters,
                        id: Math.random()*1e6|0
                    })
                });
                if (!res.ok) throw new Error(res.status);
                const payload = await res.json();
                if (payload.error) throw new Error(payload.error.message);
                this.state.dashboardData = payload.result || {};
                this.updateCardCounts(this.state.dashboardData);
            } catch (e) {
                console.error(e);
                this.updateErrorState(true, 'Failed to load dashboard');
            } finally {
                this.updateLoadingState(false);
            }
        }

        updateModalLoadingState(isLoading) {
            if (this.elements.modalLoading)
                this.elements.modalLoading.style.display = isLoading ? '' : 'none';
            if (this.elements.modalEmpty) this.elements.modalEmpty.style.display='none';
            if (this.elements.modalTable) this.elements.modalTable.style.display='none';
        }

        updateModalContent(data) {
            if (!data?.length) {
                if (this.elements.modalEmpty)
                    this.elements.modalEmpty.style.display='';
                return;
            }
            const tbody = this.elements.detailTableBody;
            tbody.innerHTML = '';
            data.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                  <td>${r.name||''}</td>
                  <td>${r.client||''}</td>
                  <td>${r.status||''}</td>
                  <td>${r.scheduled_date||''}</td>`;
                tbody.appendChild(tr);
            });
            this.elements.modalTable.style.display='';
        }

        async onCardClick(cardId, title) {
            const { client, month, year } = this.state.filters;
            const params = new URLSearchParams({
                cardSelected: cardId,
                title: title,
                client,
                month,
                year
            });
            window.location.href = `/warehouse/public/dashboard/list?${params.toString()}`;
        }

        debounce(fn, wait) {
            return (...args) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => fn(...args), wait);
            };
        }
    }

    let instance;
    function initWarehouseDashboard() {
        if (!instance) {
            instance = new WarehouseDashboardController();
            instance.init();
        }
    }
    document.addEventListener('DOMContentLoaded', () => initWarehouseDashboard());
})();

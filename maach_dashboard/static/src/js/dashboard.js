odoo.define('maach_dashboard.dashboard_content', function (require) {
    "use strict";

    require('web.dom_ready');
    var utils = require('web.utils');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;  
    publicWidget.registry.PortalRequestFormWidgets = publicWidget.Widget.extend({
        selector: '#dashboard-content',
        start: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function(){
                console.log("started form request")
               
            });

        },
        willStart: function(){
            var self = this; 
            return this._super.apply(this, arguments).then(function(){
                console.log(".....")
            })
        },
        events: {
            'click .btn-close-success': function(ev){
                $('#successful_alert').hide()

            },
         },
    });

// return PortalRequestWidget;
});
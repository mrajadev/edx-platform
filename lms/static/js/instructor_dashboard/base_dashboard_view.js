(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone'],
        function($, _, Backbone) {
            var BaseDashboardView = Backbone.View.extend({
                pubSub: $.extend({},Backbone.Events),
            });
            return BaseDashboardView;
        });
}).call(this, define || RequireJS.define);

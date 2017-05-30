(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext',
        'js/discussions_management/views/divided_discussions_inline',
        'js/discussions_management/views/divided_discussions_course_wide',
        'js/instructor_dashboard/base_dashboard_view',
        'edx-ui-toolkit/js/utils/html-utils'
    ],

        function($, _, Backbone, gettext, InlineDiscussionsView, CourseWideDiscussionsView,
                 BaseDashboardView, HtmlUtils) {
            var DiscussionsView = BaseDashboardView.extend({

                events: {
                    'change .cohorts-state': 'onCohortsEnabledChanged'
                },
                initialize: function(options) {
                    this.template = HtmlUtils.template($('#discussions-tpl').text());
                    this.context = options.context;
                    this.discussionSettings = options.discussionSettings;
                    this.listenTo(this.pubSub, "cohorts:state", this.cohortStateUpdate, this)
                },

                render: function() {
                    HtmlUtils.setHtml(this.$el, this.template({}));
                    this.showDiscussionTopics();
                    return this;
                },

                getSectionCss: function(section) {
                    return ".instructor-nav .nav-item [data-section='" + section + "']";
                },

                cohortStateUpdate: function(state){
                    this.showDiscussionManagement(state['is_cohorted'])
                },

                showDiscussionManagement: function(show){
                    if (!show){
                        $('.btn-link.discussions_management').hide();
                        $('#discussions_management').hide();
                    } else {
                        $('.btn-link.discussions_management').show();
                        $('#discussions_management').show();
                    }
                },

                showDiscussionTopics: function() {
                    var dividedDiscussionsElement = this.$('.discussions-nav');
                    if (!this.CourseWideDiscussionsView) {
                        this.CourseWideDiscussionsView = new CourseWideDiscussionsView({
                            el: dividedDiscussionsElement,
                            model: this.context.courseDiscussionTopicDetailsModel,
                            discussionSettings: this.discussionSettings
                        }).render();
                    }

                    if (!this.InlineDiscussionsView) {
                        this.InlineDiscussionsView = new InlineDiscussionsView({
                            el: dividedDiscussionsElement,
                            model: this.context.courseDiscussionTopicDetailsModel,
                            discussionSettings: this.discussionSettings
                        }).render();
                    }
                }
            });
            return DiscussionsView;
        });
}).call(this, define || RequireJS.define);

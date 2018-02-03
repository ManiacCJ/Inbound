from django.conf.urls import url

from . import views


urlpatterns = [
    # mute these after deployment
    url(r'^initialize/tecnum$', views.initialize_data, {'data': 'tec-num'}),
    url(r'^initialize/nl$', views.initialize_data, {'data': 'nl'}),
    url(r'^initialize/supplier', views.initialize_data, {'data': 'supplier'}),
    url(r'^dsl/foreign-fields', views.dsl_list_display_foreign_fields),

    url(r'^sheet/tcs$', views.download_sheet_template, {'sheet': 'tcs'}),
    url(r'^sheet/buyer$', views.download_sheet_template, {'sheet': 'buyer'}),

    url(r'^entry$', views.group_ebom_by_label, name='entry'),
    url(r'^dl/wide/(?P<nl_mapping_id>[0-9]+)$', views.download_wide_table, name='dl_wide'),
    url(r'^ul/wide$', views.upload_wide_table, name='ul_wide'),
]

from django.conf.urls import url

from . import views


urlpatterns = [
    # mute these after deployment
    url(r'^initialize/tecnum$', views.initialize_data, {'data': 'tec-num'}),
    url(r'^initialize/nl$', views.initialize_data, {'data': 'nl'}),
    url(r'^initialize/supplier', views.initialize_data, {'data': 'supplier'}),
    url(r'^initialize/osrate', views.initialize_data, {'data': 'osrate'}),
    url(r'^initialize/cclocation', views.initialize_data, {'data': 'cclocation'}),
    url(r'^initialize/ccdanger', views.initialize_data, {'data': 'ccdanger'}),
    url(r'^initialize/ccsupplier', views.initialize_data, {'data': 'ccsuppliers'}),
    url(r'^initialize/ratesupplier', views.initialize_data, {'data': 'supplierrate'}),
    url(r'^initialize/truckrate', views.initialize_data, {'data': 'truckrate'}),
    url(r'^initialize/rrr', views.initialize_data, {'data': 'rrr'}),

    url(r'^dsl/foreign-fields', views.dsl_list_display_foreign_fields),
    url(r'^dsl/wide-schema', views.dsl_parse_wide_schema),

    url(r'^sheet/tcs$', views.download_sheet_template, {'sheet': 'tcs'}),
    url(r'^sheet/buyer$', views.download_sheet_template, {'sheet': 'buyer'}),
    url(r'^sheet/wide', views.download_sheet_template, {'sheet': 'wide'}),

    url(r'^entry$', views.group_ebom_by_label, name='entry'),
    url(r'^dl/wide/(?P<nl_mapping_id>[0-9]+)$', views.download_wide_table, name='dl_wide'),
    url(r'^session/clear$', views.clear_label_session, name='session_clear'),
]

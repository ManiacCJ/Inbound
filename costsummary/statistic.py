from . import models
import os
import sqlite3
from Inbound.settings import BASE_DIR
import json
from decimal import *
import pandas as pd
import numpy as np
from . import models
from decimal import *
import datetime

# configure statistic
def conf_calculation():
    models.ConfigureCalculation.objects.all().delete()
    # configures_js=models.configure_data.objects.get(id=1).data
    # configures_dict=json.loads(configures_js)
    # configures_df=pd.DataFrame(configures_dict)
    csv_path= BASE_DIR +  '/costsummary/persistence/CONF/configures.csv'
    configures_df=pd.read_csv(csv_path,encoding='utf-8',low_memory=False)
    # sqlite_path=os.path.join(BASE_DIR, 'db.sqlite3')
    con=sqlite3.connect(BASE_DIR+'/db.sqlite3')
    ebom_table=pd.read_sql("select * from costsummary_ebom",con)

    inboundpackage=pd.read_sql("select * from costsummary_inboundpackage",con)
    NominalLabelMapping=pd.read_sql("select * from costsummary_NominalLabelMapping",con)
    inboundheaderpart=pd.read_sql("select * from costsummary_inboundheaderpart",con)
    inboundcalculation=pd.read_sql("select * from costsummary_InboundCalculation",con)
    inboundaddress=pd.read_sql("select * from costsummary_inboundaddress",con)
    production=pd.read_sql("select * from costsummary_production",con)

    combine1=pd.merge(configures_df,ebom_table[['id','label_id','quantity']],left_on='id',right_on='id',how='left')
    combine2=pd.merge(combine1,inboundpackage[['bom_id','pkg_cubic_pcs']],left_on='id',right_on='bom_id',how='left')
    combine3=pd.merge(combine2,inboundheaderpart[['bom_id','color']],left_on='bom_id',right_on='bom_id',how='left')
    combine4=pd.merge(combine3,NominalLabelMapping[['id','value','plant_code']],left_on='label_id',right_on='id',how='left')
    combine5=pd.merge(combine4,inboundcalculation[['bom_id','inbound_ttl_veh','oversea_ocean_ttl_veh','oversea_air_veh','ddp_veh', \
                        'dom_truck_ttl_veh','dom_water_ttl_veh']],left_on='bom_id',right_on='bom_id',how='left')
    combine=pd.merge(combine5,inboundaddress[['bom_id','province','property','city']],left_on='bom_id',right_on='bom_id',how='left')

    # combine.to_csv(BASE_DIR +  '/costsummary/persistence/CONF/combine.csv',index=False)
    # combine= pd.read_csv(BASE_DIR +  '/costsummary/persistence/CONF/combine.csv',encoding='utf-8',low_memory=False)
    # combine.to_excel(os.path.join(BASE_DIR, 'combine.xlsx')) #print to excel
    configures_df_except_id=configures_df.drop('id',axis=1)
    configures_list=list(configures_df_except_id.columns)
    table_list = []
    for configure in configures_list:
        combine['conf_name']=configure
        table = combine[combine[configure].notnull()]
        if not table.empty:
            try:
                table_color = table[(table['color'].notnull() ) & (table['color'] != 'nan') & (table['color'] != 'None')]
                color = list(set(table_color['color']))[0]
            except:
                color = ''
            table_color = table[(table['color'].isnull()) | (table['color'] == color)]
            table_color['pkg_cubic_veh']=table_color['pkg_cubic_pcs']*table_color['quantity']      
            table_color['base']=table_color['plant_code'].str[0:2]
            table_gp=table_color.groupby(['base','plant_code','value','conf_name'],as_index=False)
            table_ib_vol=table_gp.agg({'pkg_cubic_veh':np.sum,'inbound_ttl_veh':np.sum, \
            		'oversea_ocean_ttl_veh':np.sum,'oversea_air_veh':np.sum,'ddp_veh':np.sum, \
            		'dom_truck_ttl_veh':np.sum,'dom_water_ttl_veh':np.sum})

            
            table_ib_vol['import_ib']=table_ib_vol['oversea_ocean_ttl_veh']+table_ib_vol['oversea_air_veh']
            table_ib_vol['dom_ddp_ib']=table_ib_vol['ddp_veh']
            table_ib_vol['dom_fca_ib']=table_ib_vol['dom_truck_ttl_veh']+table_ib_vol['dom_water_ttl_veh']

            table_ib_vol=table_ib_vol.rename(columns={'pkg_cubic_veh':'volume'})

            #国产、自制
            table_dom=table_color[(table_color['property']==1) | (table_color['property']==3)]
            table_dom_vol_gp=table_dom[['value','conf_name','pkg_cubic_veh']].groupby(['value','conf_name'],as_index=False)
            table_dom_vol=table_dom_vol_gp.agg({'pkg_cubic_veh':np.sum})

            table_dom_vol=table_dom_vol.rename(columns={'pkg_cubic_veh':'dom_volume'})
            #本地
            table_local=table_color[(table_color['property']==3) | 
                    ((table_color['base'] == 'SY') & ((table_color['province'] == u'浙江') |
                    (table_color['province'] == u'江苏') |
                    (table_color['province'] == u'上海'))) |
                    ((table_color['base'] == 'DY') & (table_color['province'] == u'山东'))|
                    ((table_color['base'] == 'WH') & (table_color['province'] == u'湖北')) |
                    ((table_color['base'] == 'SY') & (table_color['province'] == u'辽宁'))
                    ]

            table_local_vol_gp=table_local[['value','conf_name','pkg_cubic_veh']].groupby(['value','conf_name'],as_index=False)
            table_local_vol=table_local_vol_gp.agg({'pkg_cubic_veh':np.sum})

            table_local_vol=table_local_vol.rename(columns={'pkg_cubic_veh':'local_volume'})
            #园区
            table_park= table_color[(table_color['city'].str.contains(u'武汉园区') & (table_color['base'] == 'WH'))
                                |  (table_color['city'].str.contains(u'沈阳园区') & (table_color['base'] == 'SY'))]
            table_park_vol_np=table_park[['value','conf_name','pkg_cubic_veh']].groupby(['value','conf_name'],as_index=False)
            table_park_vol=table_park_vol_np.agg({'pkg_cubic_veh':np.sum})
            table_park_vol=table_park_vol.rename(columns={'pkg_cubic_veh':'park_volume'})

            conf_conbine1=pd.merge(table_ib_vol,table_dom_vol,left_on=['value','conf_name'],right_on=['value','conf_name'],how='left')
            conf_conbine2=pd.merge(conf_conbine1,table_local_vol,left_on=['value','conf_name'],right_on=['value','conf_name'],how='left')
            conf_conbine3=pd.merge(conf_conbine2,table_park_vol,left_on=['value','conf_name'],right_on=['value','conf_name'],how='left')
            conf_conbine=pd.merge(conf_conbine3,production,left_on=['base','plant_code','value','conf_name'],right_on=['base','plant','label','configure'],how='left')

            conf_conbine=conf_conbine.fillna(0)
            conf_conbine['dom_rate']=np.where((conf_conbine['volume'].notnull()) & (conf_conbine['volume'].apply(lambda x: x != 0)),conf_conbine['dom_volume']/conf_conbine['volume'],0)
            conf_conbine['local_rate']=np.where((conf_conbine['dom_volume'].notnull()) & (conf_conbine['dom_volume'].apply(lambda x: x != 0)),conf_conbine['local_volume']/conf_conbine['volume'],0)
            conf_conbine['park_rate']=np.where((conf_conbine['dom_volume'].notnull()) & (conf_conbine['dom_volume'].apply(lambda x: x != 0)),conf_conbine['park_volume']/conf_conbine['volume'],0)
            table_list.append(conf_conbine)
    configure_calculation = pd.concat(table_list,ignore_index=True)
    configure_calculation['model_year']=configure_calculation['value'].str.slice(-4)
    # configure_calculation['value']=configure_calculation['value'].str.slice(0,-5)
    configure_calculation = configure_calculation.sort_values(by=['value','model_year','conf_name','base'])
    for i in range(len(configure_calculation)):
        conf_calc_object = models.ConfigureCalculation.objects.filter(value=configure_calculation['value'][i],conf_name=configure_calculation['conf_name'][i],model_year=configure_calculation['model_year'][i]).first()
        if conf_calc_object is None:
            conf_calc_object = models.ConfigureCalculation(value=configure_calculation['value'][i],conf_name=configure_calculation['conf_name'][i],model_year=configure_calculation['model_year'][i])
        for char in ['base','plant_code','volume','inbound_ttl_veh','import_ib','dom_ddp_ib','dom_fca_ib','production','dom_volume','dom_rate','local_volume','local_rate','park_volume','park_rate']:
                setattr(conf_calc_object, char, configure_calculation[char][i])
        conf_calc_object.save()

# car model statistic
def model_statistic():
    path=os.path.join(BASE_DIR, 'db.sqlite3')
    con=sqlite3.connect(path)
    configurecalculation=pd.read_sql("select * from costsummary_configurecalculation",con)
    configurecalculation['volume_mul']=configurecalculation['volume']*configurecalculation['production']
    configurecalculation['inbound_ttl_veh_mul']=configurecalculation['inbound_ttl_veh']*configurecalculation['production']   
    configurecalculation['import_ib_mul']=configurecalculation['import_ib']*configurecalculation['production']   
    configurecalculation['dom_ddp_ib_mul']=configurecalculation['dom_ddp_ib']*configurecalculation['production']   
    configurecalculation['dom_fca_ib_mul']=configurecalculation['dom_fca_ib']*configurecalculation['production']   
    configurecalculation['dom_volume_mul']=configurecalculation['dom_volume']*configurecalculation['production']   
    configurecalculation['local_volume_mul']=configurecalculation['local_volume']*configurecalculation['production']   
    configurecalculation['park_volume_mul']=configurecalculation['park_volume']*configurecalculation['production']  
    model_sta_gp=configurecalculation.groupby(['base','plant_code','value','model_year'],as_index=False)

    value_gp_model=model_sta_gp.agg({'volume_mul':np.sum,'inbound_ttl_veh_mul':np.sum,'import_ib_mul':np.sum,'dom_ddp_ib_mul':np.sum, \
    			'dom_fca_ib_mul':np.sum,'production':np.sum,'dom_volume_mul':np.sum,'local_volume_mul':np.sum, \
    			'park_volume_mul':np.sum})
    value_gp_model['volume']=np.where((value_gp_model['production'].notnull()) & (value_gp_model['production'].apply(lambda x: x != 0)),value_gp_model['volume_mul']/value_gp_model['production'],0)
    value_gp_model['inbound_ttl_veh']=np.where((value_gp_model['production'].notnull()) & (value_gp_model['production'].apply(lambda x: x != 0)),value_gp_model['inbound_ttl_veh_mul']/value_gp_model['production'],0)
    value_gp_model['import_ib']=np.where((value_gp_model['production'].notnull()) & (value_gp_model['production'].apply(lambda x: x != 0)),value_gp_model['import_ib_mul']/value_gp_model['production'],0)
    value_gp_model['dom_ddp_ib']=np.where((value_gp_model['production'].notnull()) & (value_gp_model['production'].apply(lambda x: x != 0)),value_gp_model['dom_ddp_ib_mul']/value_gp_model['production'],0)
    value_gp_model['dom_fca_ib']=np.where((value_gp_model['production'].notnull()) & (value_gp_model['production'].apply(lambda x: x != 0)),value_gp_model['dom_fca_ib_mul']/value_gp_model['production'],0)
    value_gp_model['dom_volume']=np.where((value_gp_model['production'].notnull()) & (value_gp_model['production'].apply(lambda x: x != 0)),value_gp_model['dom_volume_mul']/value_gp_model['production'],0)
    value_gp_model['local_volume']=np.where((value_gp_model['production'].notnull()) & (value_gp_model['production'].apply(lambda x: x != 0)),value_gp_model['local_volume_mul']/value_gp_model['production'],0)
    value_gp_model['park_volume']=np.where((value_gp_model['production'].notnull()) & (value_gp_model['production'].apply(lambda x: x != 0)),value_gp_model['park_volume_mul']/value_gp_model['production'],0)
    value_gp_model['dom_rate']=np.where((value_gp_model['volume'].notnull()) & (value_gp_model['volume'].apply(lambda x: x != 0)),value_gp_model['dom_volume']/value_gp_model['volume'],0)
    value_gp_model['local_rate']=np.where((value_gp_model['dom_volume'].notnull()) & (value_gp_model['dom_volume'].apply(lambda x: x != 0)),value_gp_model['local_volume']/value_gp_model['volume'],0)
    value_gp_model['park_rate']=np.where((value_gp_model['dom_volume'].notnull()) & (value_gp_model['dom_volume'].apply(lambda x: x != 0)),value_gp_model['park_volume']/value_gp_model['volume'],0)

    for i in range(len(value_gp_model)):
        model_sta_object = models.ModelStatistic.objects.filter(value=value_gp_model['value'][i],model_year=value_gp_model['model_year'][i]).first()
        if model_sta_object is None:
            model_sta_object = models.ModelStatistic(value=value_gp_model['value'][i],model_year=value_gp_model['model_year'][i])
        for char in ['base','plant_code','volume','inbound_ttl_veh','import_ib','dom_ddp_ib','dom_fca_ib','production','dom_volume','dom_rate','local_volume','local_rate','park_volume','park_rate']:
            setattr(model_sta_object, char, value_gp_model[char][i])
        model_sta_object.save()

# plant statistic
def plant_statistic():
    path=os.path.join(BASE_DIR, 'db.sqlite3')
    con=sqlite3.connect(path)
    summarymodelstatistic=pd.read_sql("select * from costsummary_summarymodelstatistic",con)
    summarymodelstatistic['volume_mul']=summarymodelstatistic['volume']*summarymodelstatistic['production']
    summarymodelstatistic['inbound_ttl_veh_mul']=summarymodelstatistic['inbound_ttl_veh']*summarymodelstatistic['production']   
    summarymodelstatistic['import_ib_mul']=summarymodelstatistic['import_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_ddp_ib_mul']=summarymodelstatistic['dom_ddp_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_fca_ib_mul']=summarymodelstatistic['dom_fca_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_volume_mul']=summarymodelstatistic['dom_volume']*summarymodelstatistic['production']   
    summarymodelstatistic['local_volume_mul']=summarymodelstatistic['local_volume']*summarymodelstatistic['production']   
    summarymodelstatistic['park_volume_mul']=summarymodelstatistic['park_volume']*summarymodelstatistic['production']  
    plant_sta_gp=summarymodelstatistic.groupby(['base','plant_code','model_year'],as_index=False)
    value_gp_plant=plant_sta_gp.agg({'volume_mul':np.sum,'inbound_ttl_veh_mul':np.sum,'import_ib_mul':np.sum,'dom_ddp_ib_mul':np.sum, \
                'dom_fca_ib_mul':np.sum,'production':np.sum,'dom_volume_mul':np.sum,'local_volume_mul':np.sum, \
                'park_volume_mul':np.sum})
    value_gp_plant['volume']=np.where((value_gp_plant['production'].notnull()) & (value_gp_plant['production'].apply(lambda x: x != 0)),value_gp_plant['volume_mul']/value_gp_plant['production'],0)
    value_gp_plant['inbound_ttl_veh']=np.where((value_gp_plant['production'].notnull()) & (value_gp_plant['production'].apply(lambda x: x != 0)),value_gp_plant['inbound_ttl_veh_mul']/value_gp_plant['production'],0)
    value_gp_plant['import_ib']=np.where((value_gp_plant['production'].notnull()) & (value_gp_plant['production'].apply(lambda x: x != 0)),value_gp_plant['import_ib_mul']/value_gp_plant['production'],0)
    value_gp_plant['dom_ddp_ib']=np.where((value_gp_plant['production'].notnull()) & (value_gp_plant['production'].apply(lambda x: x != 0)),value_gp_plant['dom_ddp_ib_mul']/value_gp_plant['production'],0)
    value_gp_plant['dom_fca_ib']=np.where((value_gp_plant['production'].notnull()) & (value_gp_plant['production'].apply(lambda x: x != 0)),value_gp_plant['dom_fca_ib_mul']/value_gp_plant['production'],0)
    value_gp_plant['dom_volume']=np.where((value_gp_plant['production'].notnull()) & (value_gp_plant['production'].apply(lambda x: x != 0)),value_gp_plant['dom_volume_mul']/value_gp_plant['production'],0)
    value_gp_plant['local_volume']=np.where((value_gp_plant['production'].notnull()) & (value_gp_plant['production'].apply(lambda x: x != 0)),value_gp_plant['local_volume_mul']/value_gp_plant['production'],0)
    value_gp_plant['park_volume']=np.where((value_gp_plant['production'].notnull()) & (value_gp_plant['production'].apply(lambda x: x != 0)),value_gp_plant['park_volume_mul']/value_gp_plant['production'],0)
    value_gp_plant['dom_rate']=np.where((value_gp_plant['volume'].notnull()) & (value_gp_plant['volume'].apply(lambda x: x != 0)),value_gp_plant['dom_volume']/value_gp_plant['volume'],0)
    value_gp_plant['local_rate']=np.where((value_gp_plant['dom_volume'].notnull()) & (value_gp_plant['dom_volume'].apply(lambda x: x != 0)),value_gp_plant['local_volume']/value_gp_plant['volume'],0)
    value_gp_plant['park_rate']=np.where((value_gp_plant['dom_volume'].notnull()) & (value_gp_plant['dom_volume'].apply(lambda x: x != 0)),value_gp_plant['park_volume']/value_gp_plant['volume'],0)
    for i in range(len(value_gp_plant)):
        plant_sta_object = models.PlantStatistic.objects.filter(plant_code=value_gp_plant['plant_code'][i],model_year=value_gp_plant['model_year'][i]).first()
        if plant_sta_object is None:
            plant_sta_object = models.PlantStatistic(plant_code=value_gp_plant['plant_code'][i],model_year=value_gp_plant['model_year'][i])
        for char in ['base','plant_code','volume','inbound_ttl_veh','import_ib','dom_ddp_ib','dom_fca_ib','production','dom_volume','dom_rate','local_volume','local_rate','park_volume','park_rate']:
            setattr(plant_sta_object, char, value_gp_plant[char][i])
        plant_sta_object.save()

# base statistic
def base_statistic():
    path=os.path.join(BASE_DIR, 'db.sqlite3')
    con=sqlite3.connect(path)
    summarymodelstatistic=pd.read_sql("select * from costsummary_summarymodelstatistic",con)
    summarymodelstatistic['volume_mul']=summarymodelstatistic['volume']*summarymodelstatistic['production']
    summarymodelstatistic['inbound_ttl_veh_mul']=summarymodelstatistic['inbound_ttl_veh']*summarymodelstatistic['production']   
    summarymodelstatistic['import_ib_mul']=summarymodelstatistic['import_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_ddp_ib_mul']=summarymodelstatistic['dom_ddp_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_fca_ib_mul']=summarymodelstatistic['dom_fca_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_volume_mul']=summarymodelstatistic['dom_volume']*summarymodelstatistic['production']   
    summarymodelstatistic['local_volume_mul']=summarymodelstatistic['local_volume']*summarymodelstatistic['production']   
    summarymodelstatistic['park_volume_mul']=summarymodelstatistic['park_volume']*summarymodelstatistic['production']  
    base_sta_gp=summarymodelstatistic.groupby(['base','model_year'],as_index=False)

    value_gp_base=base_sta_gp.agg({'volume_mul':np.sum,'inbound_ttl_veh_mul':np.sum,'import_ib_mul':np.sum,'dom_ddp_ib_mul':np.sum, \
                'dom_fca_ib_mul':np.sum,'production':np.sum,'dom_volume_mul':np.sum,'local_volume_mul':np.sum, \
                'park_volume_mul':np.sum})

    value_gp_base['volume']=np.where((value_gp_base['production'].notnull()) & (value_gp_base['production'].apply(lambda x: x != 0)),value_gp_base['volume_mul']/value_gp_base['production'],0)
    value_gp_base['inbound_ttl_veh']=np.where((value_gp_base['production'].notnull()) & (value_gp_base['production'].apply(lambda x: x != 0)),value_gp_base['inbound_ttl_veh_mul']/value_gp_base['production'],0)
    value_gp_base['import_ib']=np.where((value_gp_base['production'].notnull()) & (value_gp_base['production'].apply(lambda x: x != 0)),value_gp_base['import_ib_mul']/value_gp_base['production'],0)
    value_gp_base['dom_ddp_ib']=np.where((value_gp_base['production'].notnull()) & (value_gp_base['production'].apply(lambda x: x != 0)),value_gp_base['dom_ddp_ib_mul']/value_gp_base['production'],0)
    value_gp_base['dom_fca_ib']=np.where((value_gp_base['production'].notnull()) & (value_gp_base['production'].apply(lambda x: x != 0)),value_gp_base['dom_fca_ib_mul']/value_gp_base['production'],0)
    value_gp_base['dom_volume']=np.where((value_gp_base['production'].notnull()) & (value_gp_base['production'].apply(lambda x: x != 0)),value_gp_base['dom_volume_mul']/value_gp_base['production'],0)
    value_gp_base['local_volume']=np.where((value_gp_base['production'].notnull()) & (value_gp_base['production'].apply(lambda x: x != 0)),value_gp_base['local_volume_mul']/value_gp_base['production'],0)
    value_gp_base['park_volume']=np.where((value_gp_base['production'].notnull()) & (value_gp_base['production'].apply(lambda x: x != 0)),value_gp_base['park_volume_mul']/value_gp_base['production'],0)
    value_gp_base['dom_rate']=np.where((value_gp_base['volume'].notnull()) & (value_gp_base['volume'].apply(lambda x: x != 0)),value_gp_base['dom_volume']/value_gp_base['volume'],0)
    value_gp_base['local_rate']=np.where((value_gp_base['dom_volume'].notnull()) & (value_gp_base['dom_volume'].apply(lambda x: x != 0)),value_gp_base['local_volume']/value_gp_base['volume'],0)
    value_gp_base['park_rate']=np.where((value_gp_base['dom_volume'].notnull()) & (value_gp_base['dom_volume'].apply(lambda x: x != 0)),value_gp_base['park_volume']/value_gp_base['volume'],0)
 
    for i in range(len(value_gp_base)):
        base_sta_object = models.BaseStatistic.objects.filter(base=value_gp_base['base'][i],model_year=value_gp_base['model_year'][i]).first()
        if base_sta_object is None:
            base_sta_object = models.BaseStatistic(base=value_gp_base['base'][i],model_year=value_gp_base['model_year'][i])
        for char in ['base','volume','inbound_ttl_veh','import_ib','dom_ddp_ib','dom_fca_ib','production','dom_volume','dom_rate','local_volume','local_rate','park_volume','park_rate']:
            setattr(base_sta_object, char, value_gp_base[char][i])
        base_sta_object.save()

# sgm statistic
def sgm_statistic():
    path=os.path.join(BASE_DIR, 'db.sqlite3')
    con=sqlite3.connect(path)
    summarymodelstatistic=pd.read_sql("select * from costsummary_summarymodelstatistic",con)
    summarymodelstatistic['volume_mul']=summarymodelstatistic['volume']*summarymodelstatistic['production']
    summarymodelstatistic['inbound_ttl_veh_mul']=summarymodelstatistic['inbound_ttl_veh']*summarymodelstatistic['production']   
    summarymodelstatistic['import_ib_mul']=summarymodelstatistic['import_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_ddp_ib_mul']=summarymodelstatistic['dom_ddp_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_fca_ib_mul']=summarymodelstatistic['dom_fca_ib']*summarymodelstatistic['production']   
    summarymodelstatistic['dom_volume_mul']=summarymodelstatistic['dom_volume']*summarymodelstatistic['production']   
    summarymodelstatistic['local_volume_mul']=summarymodelstatistic['local_volume']*summarymodelstatistic['production']   
    summarymodelstatistic['park_volume_mul']=summarymodelstatistic['park_volume']*summarymodelstatistic['production']  

    sgm_sta_gp=summarymodelstatistic.groupby(['model_year'],as_index=False)

    value_sgm=sgm_sta_gp.agg({'volume_mul':np.sum,'inbound_ttl_veh_mul':np.sum,'import_ib_mul':np.sum,'dom_ddp_ib_mul':np.sum, \
                'dom_fca_ib_mul':np.sum,'production':np.sum,'dom_volume_mul':np.sum,'local_volume_mul':np.sum, \
                'park_volume_mul':np.sum})

    value_sgm['company']='SGM'
    value_sgm['volume']=np.where((value_sgm['production'].notnull()) & (value_sgm['production'].apply(lambda x: x != 0)),value_sgm['volume_mul']/value_sgm['production'],0)
    value_sgm['inbound_ttl_veh']=np.where((value_sgm['production'].notnull()) & (value_sgm['production'].apply(lambda x: x != 0)),value_sgm['inbound_ttl_veh_mul']/value_sgm['production'],0)
    value_sgm['import_ib']=np.where((value_sgm['production'].notnull()) & (value_sgm['production'].apply(lambda x: x != 0)),value_sgm['import_ib_mul']/value_sgm['production'],0)
    value_sgm['dom_ddp_ib']=np.where((value_sgm['production'].notnull()) & (value_sgm['production'].apply(lambda x: x != 0)),value_sgm['dom_ddp_ib_mul']/value_sgm['production'],0)
    value_sgm['dom_fca_ib']=np.where((value_sgm['production'].notnull()) & (value_sgm['production'].apply(lambda x: x != 0)),value_sgm['dom_fca_ib_mul']/value_sgm['production'],0)
    value_sgm['dom_volume']=np.where((value_sgm['production'].notnull()) & (value_sgm['production'].apply(lambda x: x != 0)),value_sgm['dom_volume_mul']/value_sgm['production'],0)
    value_sgm['local_volume']=np.where((value_sgm['production'].notnull()) & (value_sgm['production'].apply(lambda x: x != 0)),value_sgm['local_volume_mul']/value_sgm['production'],0)
    value_sgm['park_volume']=np.where((value_sgm['production'].notnull()) & (value_sgm['production'].apply(lambda x: x != 0)),value_sgm['park_volume_mul']/value_sgm['production'],0)
    value_sgm['dom_rate']=np.where((value_sgm['volume'].notnull()) & (value_sgm['volume'].apply(lambda x: x != 0)),value_sgm['dom_volume']/value_sgm['volume'],0)
    value_sgm['local_rate']=np.where((value_sgm['dom_volume'].notnull()) & (value_sgm['dom_volume'].apply(lambda x: x != 0)),value_sgm['local_volume']/value_sgm['volume'],0)
    value_sgm['park_rate']=np.where((value_sgm['dom_volume'].notnull()) & (value_sgm['dom_volume'].apply(lambda x: x != 0)),value_sgm['park_volume']/value_sgm['volume'],0)
 
    for i in range(len(value_sgm)):
        sgm_sta_object = models.SummaryStatistic.objects.filter(company='SGM',model_year=value_sgm['model_year'][i]).first()
        if sgm_sta_object is None:
            sgm_sta_object = models.SummaryStatistic(company='SGM',model_year=value_sgm['model_year'][i])
        for char in ['volume','inbound_ttl_veh','import_ib','dom_ddp_ib','dom_fca_ib','production','dom_volume','dom_rate','local_volume','local_rate','park_volume','park_rate']:
            setattr(sgm_sta_object, char, value_sgm[char][i])
        sgm_sta_object.save()

# 未来五年车型级别报表
def future_model_table():
    # pass
    path=os.path.join(BASE_DIR, 'db.sqlite3')
    con=sqlite3.connect(path)
    old_model_statistic=pd.read_sql("select * from costsummary_modelstatistic",con)
    new_model_statistic=pd.read_sql("select * from costsummary_newmodelstatistic",con)
    model_statistic=pd.concat([old_model_statistic,new_model_statistic],axis=0,ignore_index=True)
    for i in range(len(model_statistic)):
        future_model_object = models.SummaryModel.objects.filter(
                value=model_statistic['value'][i],
                model_year=model_statistic['model_year'][i]
                ).first()
        if future_model_object is None:
            future_model_object = models.SummaryModel(
                value=model_statistic['value'][i],
                model_year=model_statistic['model_year'][i]
                )
        for char in ['base','plant_code','volume','inbound_ttl_veh','import_ib','dom_ddp_ib','dom_fca_ib','production','dom_volume','dom_rate','local_volume','local_rate','park_volume','park_rate']:
            setattr(future_model_object, char, model_statistic[char][i])
        future_model_object.save()

#未来五年车型级别报表计算
def summary_model_calculate():
    # pass
    path=os.path.join(BASE_DIR, 'db.sqlite3')
    con=sqlite3.connect(path)
    modelstatistic=pd.read_sql("select * from costsummary_summarymodel",con)
    rate=pd.read_sql("select * from costsummary_futurerate",con)
    production=pd.read_sql("select * from costsummary_production",con)

    df_mark = pd.DataFrame({'mark':'mark','year':[9999,9999,9999,9999,9999,9999,9999,9999]})
    modelstatistic['mark']='mark'
    rate=rate.rename(columns={'dom_rate':'dom_decline_rate'})
    merge1=pd.merge(modelstatistic,df_mark,left_on='mark',right_on='mark',how='left')
    merge1['index']=merge1.index
    merge1['year']=np.where(merge1['value']==merge1['value'].shift(1),merge1['model_year']+merge1['index']%8,merge1['model_year'])

    merge2=pd.merge(merge1,rate,left_on='year',right_on='year',how='left')
    data=merge2.fillna(0)
    
    #进口ib
    data['import_ib_shift']=np.where(data['year']==data['model_year'],data['import_ib'],0)   
    data['import_ib_shift']=np.where(data['year']==data['model_year']+1,data['import_ib_shift'].shift(1)*data['import_rate'],data['import_ib_shift'])
    data['import_ib_shift']=np.where(data['year']==data['model_year']+2,data['import_ib_shift'].shift(1)*data['import_rate'],data['import_ib_shift'])
    data['import_ib_shift']=np.where(data['year']==data['model_year']+3,data['import_ib_shift'].shift(1)*data['import_rate'],data['import_ib_shift'])
    data['import_ib_shift']=np.where(data['year']==data['model_year']+4,data['import_ib_shift'].shift(1)*data['import_rate'],data['import_ib_shift'])
    data['import_ib_shift']=np.where(data['year']==data['model_year']+5,data['import_ib_shift'].shift(1)*data['import_rate'],data['import_ib_shift'])
    data['import_ib_shift']=np.where(data['year']==data['model_year']+6,data['import_ib_shift'].shift(1)*data['import_rate'],data['import_ib_shift'])
    data['import_ib_shift']=np.where(data['year']==data['model_year']+7,data['import_ib_shift'].shift(1)*data['import_rate'],data['import_ib_shift'])

    #国产ddp ib
    data['dom_ddp_ib_shift']=np.where(data['year']==data['model_year'],data['dom_ddp_ib'],0)   
    data['dom_ddp_ib_shift']=np.where(data['year']==data['model_year']+1,data['dom_ddp_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_ddp_ib_shift'])
    data['dom_ddp_ib_shift']=np.where(data['year']==data['model_year']+2,data['dom_ddp_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_ddp_ib_shift'])
    data['dom_ddp_ib_shift']=np.where(data['year']==data['model_year']+3,data['dom_ddp_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_ddp_ib_shift'])
    data['dom_ddp_ib_shift']=np.where(data['year']==data['model_year']+4,data['dom_ddp_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_ddp_ib_shift'])
    data['dom_ddp_ib_shift']=np.where(data['year']==data['model_year']+5,data['dom_ddp_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_ddp_ib_shift'])
    data['dom_ddp_ib_shift']=np.where(data['year']==data['model_year']+6,data['dom_ddp_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_ddp_ib_shift'])
    data['dom_ddp_ib_shift']=np.where(data['year']==data['model_year']+7,data['dom_ddp_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_ddp_ib_shift'])

    #国产fca ib
    data['dom_fca_ib_shift']=np.where(data['year']==data['model_year'],data['dom_fca_ib'],0)   
    data['dom_fca_ib_shift']=np.where(data['year']==data['model_year']+1,data['dom_fca_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_fca_ib_shift'])
    data['dom_fca_ib_shift']=np.where(data['year']==data['model_year']+2,data['dom_fca_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_fca_ib_shift'])
    data['dom_fca_ib_shift']=np.where(data['year']==data['model_year']+3,data['dom_fca_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_fca_ib_shift'])
    data['dom_fca_ib_shift']=np.where(data['year']==data['model_year']+4,data['dom_fca_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_fca_ib_shift'])
    data['dom_fca_ib_shift']=np.where(data['year']==data['model_year']+5,data['dom_fca_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_fca_ib_shift'])
    data['dom_fca_ib_shift']=np.where(data['year']==data['model_year']+6,data['dom_fca_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_fca_ib_shift'])
    data['dom_fca_ib_shift']=np.where(data['year']==data['model_year']+7,data['dom_fca_ib_shift'].shift(1)*data['dom_decline_rate'],data['dom_fca_ib_shift'])
    
    #删除多余的列
    data['model_year']=data['year']
    data = data.drop(['import_ib','dom_ddp_ib','dom_fca_ib'],axis=1)
    data = data.rename(columns={'import_ib_shift':'import_ib','dom_ddp_ib_shift':'dom_ddp_ib','dom_fca_ib_shift':'dom_fca_ib'})
    data['inbound_ttl_veh']=data['import_ib']+data['dom_ddp_ib']+data['dom_fca_ib']


    data=data.drop('production',axis=1)
    production=production.rename(columns={'label':'value','prd_year':'model_year'})
    production_sum=production[['value','model_year','production']].groupby(['value','model_year'],as_index=False).sum()
    future=pd.merge(data,production_sum, \
             left_on=['value','model_year'],right_on=['value','model_year'],how='left')
    year = int(datetime.date.today().strftime('%Y'))
    future=future[future['model_year']<=year+5]
    future=future.reset_index(drop=True)
    for i in range(len(future)):
        future_object = models.SummaryModelStatistic.objects.filter(
                value=future['value'][i],
                model_year=future['model_year'][i]
                ).first()
        if future_object is None:
            future_object = models.SummaryModelStatistic(
                value=future['value'][i],
                model_year=future['model_year'][i]
                )
        for char in ['base','plant_code','volume','inbound_ttl_veh','import_ib','dom_ddp_ib', \
            'dom_fca_ib','production','dom_volume','dom_rate','local_volume','local_rate','park_volume','park_rate']:
            setattr(future_object, char, future[char][i])
        future_object.save()

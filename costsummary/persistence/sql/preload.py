import os
import sys
import csv
import sqlite3
import cx_Oracle

conn = cx_Oracle.connect('WSTCMS', 'Pass1124', '10.203.45.169:1534/TCMS.SGM.COM')
cursor = conn.cursor()

if sys.platform == 'win32':
    django_db = 'D:\\sgmuserprofile\\siz5v8\\Documents\\Solutions\\Inbound\\db.sqlite3'
    preload_dir = 'D:\\sgmuserprofile\\siz5v8\\Documents\\Solutions\\Inbound\\preload'

elif sys.platform == 'linux':
    django_db = '/midware/cron/db.sqlite3'
    preload_dir = '/midware/data/ib-preload'

else:
    raise AssertionError


conn = sqlite3.connect(django_db)
c = conn.cursor()

c.execute("SELECT id, value, book, plant_code, model FROM costsummary_nominallabelmapping")
param_tuples = list(c.fetchall())

c.close()
conn.close()

print(param_tuples)


_sql = """
SELECT
    MIN(ID),
    MODEL_YEAR,
    BOOK,
    PLANT_CODE,
    MODEL,
    PACKAGE,
    MIN(COLOR),
    UPC,
    FNA,
    COMPONENT_MATERIAL_NUMBER,
    MIN(COMPONENT_MATERIAL_DESC_C),
    MIN(COMPONENT_MATERIAL_DESC_E),
    HEADER_PART_NUMBER,
    AR_EM_MATERIAL_FLAG,
    WORKSHOP,
    DUNS_NUMBER,
    MIN(VENDOR_NAME),
    EWO_NUMBER,
    MIN(MODEL_OPTION),
    VPPS,
    USAGE_STATUS,
    MIN(VALID_FROM_DATE),
    MIN(VALID_TO_DATE),
    MIN(AGG_PACKAGE_DESC),
    MIN(AGG_ORDER_SAMPLE),
    MIN(AGG_USAGE_QTY),
    MIN(ETL_TIME)
    
    FROM OWTCMS.TA_AGG_EBOM
    
    WHERE BOOK = '{0}' AND PLANT_CODE = '{1}' AND MODEL = '{2}' 
    
    GROUP BY
        MODEL_YEAR,
        BOOK,
        PLANT_CODE,
        MODEL,
        PACKAGE,
        UPC,
        FNA,
        COMPONENT_MATERIAL_NUMBER,
        HEADER_PART_NUMBER,
        AR_EM_MATERIAL_FLAG,
        WORKSHOP,
        DUNS_NUMBER,
        EWO_NUMBER,
        VPPS,
        USAGE_STATUS
        
    ORDER BY MODEL_YEAR
"""


for param in param_tuples:
    sql = _sql.format(param[2], param[3], param[4])
    cursor.execute(sql)

    with open(os.path.join(preload_dir, str(param[0]) + '.csv'), 'w+', encoding='utf8') as csvfile:
        w = csv.writer(csvfile, delimiter=',')

        for x in cursor.fetchall():
            w.writerow(x)

import csv


index = 0
fields = []
types = []

sql = """
create table ta_ebom (
    ID INTEGER PRIMARY KEY, 
"""

with open('ta-ebom-sample.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')

    for row in reader:
        if index == 0:  # header

            for cell in row:
                fields.append(cell.strip())

        elif index == 1:
            for cell in row:

                try:
                    f_val = float(cell.strip())

                except ValueError as e:
                    types.append('TEXT')

                else:

                    try:
                        int_val = int(cell.strip())

                    except ValueError as e:
                        types.append('REAL')

                    else:
                        types.append('INTEGER')

        else:
            break

        index += 1

for i in range(1, len(fields)):

    if i != len(fields) - 1:
        sql += f'{fields[i]} {types[i]}, \n'

    else:
        sql += f'{fields[i]} {types[i]}\n)'


print(sql)


create_ta_ebom_table = """
create table ta_ebom (
    ID INTEGER PRIMARY KEY, 
    BOOK TEXT, 
    MODEL_YEAR INTEGER, 
    PLANT_CODE TEXT, 
    PACKAGE TEXT, 
    COLOR TEXT, 
    MODEL TEXT, 
    UPC TEXT, 
    FNA TEXT, 
    COMPONENT_VARIANT_NUMBER TEXT, 
    COUNTER INTEGER, 
    BOM_PATH TEXT, 
    COMPONENT_MATERIAL_NUMBER TEXT, 
    VALID_FROM_DATE INTEGER, 
    VALID_TO_DATE INTEGER, 
    PACKAGE_DESC TEXT, 
    COLOR_DESC TEXT, 
    MODEL_DESC TEXT, 
    COMPONENT_MATERIAL_DESC_C TEXT, 
    COMPONENT_MATERIAL_DESC_E TEXT, 
    HAND TEXT, 
    USAGE_QTY INTEGER, 
    UNIT_OF_MEASURE TEXT, 
    USAGE_STATUS TEXT, 
    AR_EM_MATERIAL_FLAG TEXT, 
    WORKSHOP TEXT, 
    SUPPLY_AREA TEXT, 
    DUNS_NUMBER TEXT, 
    VENDOR_NAME TEXT, 
    EWO_NUMBER TEXT, 
    MODEL_CODE TEXT, 
    MODEL_OPTION TEXT, 
    OPTIONAL_PART_GROUP TEXT, 
    OPTIONAL_PART_RELATED TEXT, 
    FAMILY_ADDRESS TEXT, 
    BROADCAST_CODE TEXT, 
    DORMANT_STATUS TEXT, 
    DELETION_FLAG TEXT, 
    LOADED_DATE REAL, 
    LAST_UPDATED_DATE REAL, 
    COMPONENT_VARIANT_NAME TEXT, 
    HEADER_PART_NUMBER INTEGER, 
    STRUCTURE_NODE_DESC_E TEXT, 
    STRUCTURE_NODE_DESC_C TEXT, 
    ALTERNATIVE_EWO_NUMBER TEXT, 
    ORDER_SAMPLE TEXT, 
    OS_FLAG INTEGER, 
    SPECIAL_PROCUREMENT_TYPE INTEGER, 
    MATERIAL_STATUS TEXT, 
    ENGINEER_CODE TEXT, 
    REPLACEMENT TEXT, 
    VPPS TEXT
)
"""
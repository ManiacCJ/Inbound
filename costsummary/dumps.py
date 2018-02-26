import os
import csv
from django.db import IntegrityError
from django.shortcuts import Http404
from django.core.exceptions import ValidationError

from . import models

# Persistence directory
PERSISTENCE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'persistence'
)


class InitializeData:
    """ Load initial csv-formatted data. """

    @staticmethod
    def load_initial_tec_num(in_file='TEC/tec.csv') -> int:
        """ Load sgm plant data into backend database. """
        print("Start loading...")

        # delete all existed records
        models.TecCore.objects.all().delete()

        with open(os.path.join(PERSISTENCE_DIR, in_file), encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            for row in reader:
                if index > 0:  # skip header
                    tec_id = int(row[0].strip())
                    common_part_name = row[1].strip()
                    mgo = row[2].strip()

                    t = models.TecCore(
                        tec_id=tec_id,
                        common_part_name=common_part_name.upper(),  # upper case
                        mgo_part_name_list=mgo.upper()
                    )

                    # save models
                    t.save()

                # print(index)
                index += 1

        # return loaded row number
        return index

    @staticmethod
    def load_initial_nl_mapping(in_file='TEC/nl-mapping.csv'):
        """ Generate nominal label mapping according to book, plant and model. """
        print("Start loading...")

        # delete existed objects
        models.NominalLabelMapping.objects.all().delete()

        # find csv file path
        with open(os.path.join(PERSISTENCE_DIR, in_file), encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            for row in reader:
                if index > 0:  # skip header
                    book = row[0].strip()
                    plant_code = row[1].strip()
                    model = row[2].strip()
                    value = row[3].strip()

                    try:
                        i = models.NominalLabelMapping(
                            book=book,
                            plant_code=plant_code,
                            model=model,
                            value=value
                        )

                        # save models
                        i.save()

                    # unique constraints not meet
                    except (IntegrityError, ValidationError) as e:
                        print(e)
                        continue

                # print(index)
                index += 1

            # return loaded row number
            return index

    @staticmethod
    def load_initial_os_rate(in_file='TEC/os-rate.csv'):
        """ Load initial oversea rate. """
        print("Start loading...")

        # delete existed objects
        models.InboundOverseaRate.objects.all().delete()

        # find csv file path
        with open(os.path.join(PERSISTENCE_DIR, in_file), encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # reverse mapping of base
            REV_BASE_CHOICE = dict()
            for _i, _s in models.BASE_CHOICE:
                if _i >= 0:  # exclude 3rd party
                    REV_BASE_CHOICE[_s] = _i

            # row index
            index = 0

            for row in reader:
                if index >= 0:  # no header
                    region = row[0].strip().upper()
                    base = REV_BASE_CHOICE[row[1].strip().upper()]
                    cc = row[2].strip().upper()
                    export_harbor = row[3].strip().upper()
                    definition_harbor = row[4].strip().upper()
                    os_dm_rate = float(row[5].strip()) if row[5].strip() else None
                    cc_rate = float(row[6].strip()) if row[6].strip() else None
                    euro_doc_rate = float(row[7].strip()) if row[7].strip() else None
                    os_40h_rate = float(row[8].strip()) if row[8].strip() else None
                    os_40h_danger_rate = float(row[9].strip()) if row[9].strip() else None
                    inter_40h_rate = float(row[10].strip()) if row[10].strip() else None
                    inter_40h_danger_rate = float(row[11].strip()) if row[11].strip() else None
                    dm_40h_rate = float(row[12].strip()) if row[12].strip() else None
                    dm_40h_danger_rate = float(row[13].strip()) if row[13].strip() else None
                    delegate = float(row[14].strip()) if row[14].strip() else None
                    delegate_danger = float(row[15].strip()) if row[15].strip() else None
                    vol_40h = float(row[16].strip()) if row[16].strip() else None
                    load_rate = float(row[17].strip()) if row[17].strip() else None
                    cpc = float(row[18].strip()) if row[18].strip() else None
                    cpc_danger = float(row[19].strip()) if row[19].strip() else None

                    try:
                        i = models.InboundOverseaRate(
                            region=region,
                            base=base,
                            cc=cc,
                            export_harbor=export_harbor,
                            definition_harbor=definition_harbor,
                            os_dm_rate=os_dm_rate,
                            cc_rate=cc_rate,
                            euro_doc_rate=euro_doc_rate,
                            os_40h_rate=os_40h_rate,
                            os_40h_danger_rate=os_40h_danger_rate,
                            inter_40h_rate=inter_40h_rate,
                            inter_40h_danger_rate=inter_40h_danger_rate,
                            dm_40h_rate=dm_40h_rate,
                            dm_40h_danger_rate=dm_40h_danger_rate,
                            delegate=delegate,
                            delegate_danger=delegate_danger,
                            vol_40h=vol_40h,
                            load_rate=load_rate,
                            cpc=cpc,
                            cpc_danger=cpc_danger,
                        )

                        # save models
                        i.save()

                    # unique constraints not meet
                    except (IntegrityError, ValidationError) as e:
                        print(e)
                        continue

                # print(index)
                index += 1

            # return loaded row number
            return index

    @staticmethod
    def load_initial_distance(in_file='supplier/supplier-distance-new.csv'):
        print("Start loading...")

        # delete all existed records
        models.Supplier.objects.all().delete()
        models.SupplierDistance.objects.all().delete()

        # parse distance and comment from original data like '804（烟大线）'
        def parse_distance(distance_cell: str) -> tuple:
            # blank cell
            if not distance_cell.strip():
                return None, None

            distance_as_number, _comment = None, None

            try:
                # no comment
                distance_as_number = float(distance_cell)

            except ValueError:
                # find parentheses
                if distance_cell.find('（') != -1 and distance_cell.find('）') != -1:
                    left = distance_cell.find('（')
                    right = distance_cell.find('）')

                    if left != 0:
                        distance_as_number = float(distance_cell[0: left].strip())
                    else:
                        distance_as_number = None
                    _comment = distance_cell[left + 1: right].strip()
                # find parentheses
                elif distance_cell.find('(') != -1 and distance_cell.find(')') != -1:
                    left = distance_cell.find('(')
                    right = distance_cell.find(')')

                    if left != 0:
                        distance_as_number = float(distance_cell[0: left].strip())
                    else:
                        distance_as_number = None
                    _comment = distance_cell[left + 1: right].strip()
                else:
                    raise Exception

            else:
                _comment = None

            finally:
                return distance_as_number, _comment

        # find csv file path
        csv_path = os.path.join(PERSISTENCE_DIR, in_file)

        with open(csv_path, encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            # reverse mapping of base
            REV_BASE_CHOICE = dict()
            for _i, _s in models.BASE_CHOICE:
                if _i >= 0:  # exclude 3rd party
                    REV_BASE_CHOICE[_s] = _i

            for row in reader:
                if index > 0:  # skip header

                    if not row[3].strip():  # primary key is the 4-th column (the duns)
                        break

                    original_source = row[0].strip() if row[0].strip() else None

                    row_1 = row[1].strip()
                    if row_1:
                        if row_1 == 'Y' or row_1 == 'y':
                            is_mono_address = True
                        elif row_1 == 'N' or row_1 == 'n':
                            is_mono_address = False
                        else:
                            print(row_1)
                            raise Exception
                    else:
                        is_mono_address = None

                    row_2 = row[2].strip()
                    if row_2:
                        if row_2 == 'Y' or row_2 == 'y':
                            is_promised_address = True
                        elif row_2 == 'N' or row_2 == 'n':
                            is_promised_address = False
                        else:
                            print(row_2)
                            raise Exception
                    else:
                        is_promised_address = None

                    duns = row[3].strip()
                    name = row[4].strip()
                    address = row[5].strip()

                    post_code = row[6].strip()
                    region = row[7].strip()
                    province = row[8].strip()
                    district = row[9].strip()

                    comment = row[14].strip() if row[14].strip() else None

                    row_15 = row[15].strip()
                    if row_15:
                        if row_15 == 'Y' or row_15 == 'y':
                            is_removable = True
                        elif row_15 == 'N' or row_15 == 'n':
                            is_removable = False
                        else:
                            print(row_15)
                            raise Exception
                    else:
                        is_removable = None

                    # save model
                    s = models.Supplier(
                        original_source=original_source,
                        is_mono_address=is_mono_address,
                        is_promised_address=is_promised_address,
                        duns=duns,
                        name=name,
                        address=address,
                        post_code=post_code,
                        region=region,
                        province=province,
                        district=district,

                        comment=comment,
                        is_removable=is_removable
                    )

                    s.save()

                    # distance to four bases: JQ, DY, NS, WH
                    jq = parse_distance(row[10].strip())
                    dy = parse_distance(row[11].strip())
                    ns = parse_distance(row[12].strip())
                    wh = parse_distance(row[13].strip())

                    # save distance
                    jd_object = models.SupplierDistance(
                        base=REV_BASE_CHOICE['JQ'],
                        distance=jq[0],
                        supplier=s,
                        comment=jq[1]
                    )
                    jd_object.save()

                    dy_object = models.SupplierDistance(
                        base=REV_BASE_CHOICE['DY'],
                        distance=dy[0],
                        supplier=s,
                        comment=dy[1]
                    )
                    dy_object.save()

                    ns_object = models.SupplierDistance(
                        base=REV_BASE_CHOICE['NS'],
                        distance=ns[0],
                        supplier=s,
                        comment=ns[1]
                    )
                    ns_object.save()

                    wh_object = models.SupplierDistance(
                        base=REV_BASE_CHOICE['WH'],
                        distance=wh[0],
                        supplier=s,
                        comment=wh[1]
                    )
                    wh_object.save()

                index += 1

        return index


class ParseArray:
    """ Parse two-dimensional array of excel. """

    @staticmethod
    def parse_tcs(matrix: list):
        """ Parse TCS data. """
        # tcs header
        TCS_HEADER = [
            {'r_offset': 0, 'ex_header': 'P/N', 'in_header': 'bom:part_number'},
            {'r_offset': 0, 'ex_header': 'Bidderlist No.', 'in_header': 'bidder_list_number'},
            {'r_offset': 0, 'ex_header': 'Program', 'in_header': 'program'},
            {'r_offset': 0, 'ex_header': 'Supplier Address', 'in_header': 'supplier_ship_from_address'},
            {'r_offset': 0, 'ex_header': 'Process', 'in_header': 'process', 'match_display': True},
            {'r_offset': 0, 'ex_header': 'Suggest Delivery Method', 'in_header': 'suggest_delivery_method',
             'match_display': True},
            {'r_offset': 0, 'ex_header': 'SGM\'s Transport Duty', 'in_header': 'sgm_transport_duty',
             'match_display': True},
            {'r_offset': 0, 'ex_header': 'Supplier\'s Transport Duty', 'in_header': 'supplier_transport_duty',
             'match_display': True},
            {'r_offset': 0, 'ex_header': 'SGM\'s Returnable Package Duty', 'in_header': 'sgm_returnable_duty',
             'match_display': True},
            {'r_offset': 0, 'ex_header': 'Supplier\'s Returnable Package Duty',
             'in_header': 'supplier_returnable_duty', 'match_display': True},
            {'r_offset': -1, 'ex_header': '外协加工业务模式\nConsignment Mode', 'in_header': 'consignment_mode',
             'match_display': True},

            {'r_offset': 0, 'ex_header': 'Container Name', 'in_header': 'supplier_pkg_name'},
            {'r_offset': 0, 'ex_header': 'Quantity', 'in_header': 'supplier_pkg_pcs'},
            {'r_offset': 0, 'ex_header': 'Length', 'in_header': 'supplier_pkg_length'},
            {'r_offset': 0, 'ex_header': 'Height', 'in_header': 'supplier_pkg_height'},
            {'r_offset': 0, 'ex_header': 'Width', 'in_header': 'supplier_pkg_width'},

            {'r_offset': 0, 'ex_header': 'GM_PKG_CONTAINER_NAME', 'in_header': 'sgm_pkg_name'},
            {'r_offset': 0, 'ex_header': 'GM_PKG_QTY', 'in_header': 'sgm_pkg_pcs'},
            {'r_offset': 0, 'ex_header': 'GM_PKG_LENGTH', 'in_header': 'sgm_pkg_length'},
            {'r_offset': 0, 'ex_header': 'GM_PKG_WIDTH', 'in_header': 'sgm_pkg_width'},
            {'r_offset': 0, 'ex_header': 'GM_PKG_HEIGHT', 'in_header': 'sgm_pkg_height'},
        ]

        for i in range(len(TCS_HEADER)):
            TCS_HEADER[i]['ex_header'] = TCS_HEADER[i]['ex_header'].upper()  # upper-case

        # cursor
        for i in range(len(matrix)):
            all_header_found = True

            # all header field found
            for dict_obj in TCS_HEADER:
                if 'col' not in dict_obj:
                    all_header_found = False
                    break

            if all_header_found:
                break

            row = matrix[i]

            for j in range(len(row)):
                cell = str(row[j])

                for k in range(len(TCS_HEADER)):
                    if cell.strip().upper() == TCS_HEADER[k]['ex_header']:
                        TCS_HEADER[k]['col'] = j
                        TCS_HEADER[k]['row'] = i

        # check header row
        data_row = None

        for dict_obj in TCS_HEADER:
            if 'col' not in dict_obj or 'row' not in dict_obj:
                raise Http404(f'数据列{dict_obj["ex_header"]}没有找到')
            else:
                if data_row is not None:
                    if dict_obj['row'] - dict_obj['r_offset'] != data_row:
                        raise Http404('Excel 格式不正确.')
                else:
                    data_row = dict_obj['row'] + dict_obj['r_offset']

        # start parsing row
        start_row = data_row + 1

        for row in matrix[start_row:]:
            lookup_value = row[TCS_HEADER[0]['col']]

            # if no actual value
            if lookup_value == '':
                continue

            try:
                tcs_objects = models.InboundTCS.objects.filter(bom__part_number=int(lookup_value))

            except ValueError as e:
                print(e)
                pass

            else:
                for tcs_object in tcs_objects:
                    params = dict()

                    for dict_obj in TCS_HEADER[1: -10]:
                        if 'match_display' in dict_obj:
                            choice = getattr(tcs_object, dict_obj['in_header'] + '_choice')

                            for int_val, str_val in choice:
                                if row[dict_obj['col']].strip().upper() == str_val.upper():
                                    params[dict_obj['in_header']] = int_val
                                    break

                        else:
                            params[dict_obj['in_header']] = row[dict_obj['col']]

                    for attribute in params:
                        if params[attribute] == '':
                            params[attribute] = None
                        setattr(tcs_object, attribute, params[attribute])

                    tcs_object.save()

            try:
                tcs_package_objects = models.InboundTCSPackage.objects.filter(bom__part_number=int(lookup_value))

            except ValueError as e:
                print(e)
                pass

            else:
                for tcs_package_object in tcs_package_objects:
                    params = dict()

                    for dict_obj in TCS_HEADER[-10:]:
                        if 'match_display' in dict_obj:
                            choice = getattr(tcs_package_object, dict_obj['in_header'] + '_choice')

                            for int_val, str_val in choice:
                                if row[dict_obj['col']].strip().upper() == str_val.upper():
                                    params[dict_obj['in_header']] = int_val
                                    break

                        else:
                            params[dict_obj['in_header']] = row[dict_obj['col']]

                    for attribute in params:
                        if params[attribute] == '':
                            params[attribute] = None
                        setattr(tcs_package_object, attribute, params[attribute])

                    tcs_package_object.save()

    @staticmethod
    def parse_buyer(matrix: list):
        """ Parse TCS data. """
        # buyer header
        BUYER_HEADER = [
            {'r_offset': 0, 'ex_header': '零件号', 'in_header': 'bom:part_number'},
            {'r_offset': 0, 'ex_header': '采购员', 'in_header': 'buyer'},
            {'r_offset': 0, 'ex_header': '计量单位', 'in_header': 'contract_incoterm'},
            {'r_offset': 0, 'ex_header': '运输费用', 'in_header': 'contract_supplier_transportation_cost'},
            {'r_offset': 0, 'ex_header': '外包装费用', 'in_header': 'contract_supplier_pkg_cost'},
            {'r_offset': 0, 'ex_header': '排序费用', 'in_header': 'contract_supplier_seq_cost'},
        ]

        for i in range(len(BUYER_HEADER)):
            BUYER_HEADER[i]['ex_header'] = BUYER_HEADER[i]['ex_header'].upper()  # upper-case

        # cursor
        for i in range(len(matrix)):
            all_header_found = True

            # all header field found
            for dict_obj in BUYER_HEADER:
                if 'col' not in dict_obj:
                    all_header_found = False
                    break

            if all_header_found:
                break

            row = matrix[i]

            for j in range(len(row)):
                cell = str(row[j])

                for k in range(len(BUYER_HEADER)):
                    if cell.strip().upper() == BUYER_HEADER[k]['ex_header']:
                        BUYER_HEADER[k]['col'] = j
                        BUYER_HEADER[k]['row'] = i

        # check header row
        data_row = None

        for dict_obj in BUYER_HEADER:
            if 'col' not in dict_obj or 'row' not in dict_obj:
                raise Http404(f'数据列{dict_obj["ex_header"]}没有找到')
            else:
                if data_row is not None:
                    if dict_obj['row'] - dict_obj['r_offset'] != data_row:
                        raise Http404('Excel 格式不正确.')
                else:
                    data_row = dict_obj['row'] + dict_obj['r_offset']

        # start parsing row
        start_row = data_row + 1

        for row in matrix[start_row:]:
            lookup_value = row[BUYER_HEADER[0]['col']]

            # if no actual value
            if lookup_value == '':
                continue

            try:
                buyer_objects = models.InboundBuyer.objects.filter(bom__part_number=int(lookup_value))

            except ValueError as e:
                print(e)
                pass

            else:
                for buyer_object in buyer_objects:
                    params = dict()

                    for dict_obj in BUYER_HEADER[1:]:
                        if 'match_display' in dict_obj:
                            choice = getattr(buyer_object, dict_obj['in_header'] + '_choice')

                            for int_val, str_val in choice:
                                if row[dict_obj['col']].strip().upper() == str_val.upper():
                                    params[dict_obj['in_header']] = int_val
                                    break

                        else:
                            params[dict_obj['in_header']] = row[dict_obj['col']]

                    for attribute in params:
                        if params[attribute] == '':
                            params[attribute] = None
                        setattr(buyer_object, attribute, params[attribute])

                    buyer_object.save()

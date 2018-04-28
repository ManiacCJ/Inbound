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
    def load_initial_cc_location(in_file='TEC/cc-locations.csv'):
        """ Load cc location. """
        print("Start loading...")

        # delete existed objects
        models.InboundCcLocations.objects.all().delete()

        # find csv file path
        with open(os.path.join(PERSISTENCE_DIR, in_file), encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            for row in reader:
                if index >= 0:  # skip header
                    cc_group = int(row[0].strip())
                    cn_location_name = row[1].strip()
                    en_location_name = row[2].strip().upper()
                    currency_unit = int(row[3].strip())
                    per_cbm = float(row[4].strip()) if row[4].strip() else None
                    cc = row[5].strip().upper()

                    try:
                        c = models.InboundCcLocations(
                            cc_group=cc_group,
                            cn_location_name=cn_location_name,
                            en_location_name=en_location_name,
                            currency_unit=currency_unit,
                            per_cbm=per_cbm,
                            cc=cc
                        )

                        # save models
                        c.save()

                    # unique constraints not meet
                    except (IntegrityError, ValidationError) as e:
                        print(e)
                        continue

                # print(index)
                index += 1

            # return loaded row number
            return index

    @staticmethod
    def load_initial_cc_danger(in_file='TEC/cc-danger.csv'):
        """ Load cc location. """
        print("Start loading...")

        # delete existed objects
        models.InboundDangerPackage.objects.all().delete()

        # find csv file path
        with open(os.path.join(PERSISTENCE_DIR, in_file), encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            for row in reader:
                if index > 0:  # skip header
                    from_to_type = int(row[0].strip())
                    from_one = row[1].strip().upper()
                    to_one = row[2].strip().upper()
                    standard = float(row[3].strip()) if row[3].strip() else None
                    danger = float(row[4].strip()) if row[4].strip() else None

                    d = models.InboundDangerPackage(
                        from_to_type=from_to_type,
                        from_one=from_one,
                        to_one=to_one,
                        standard=standard,
                        danger=danger,
                    )

                    # save models
                    d.save()

                # print(index)
                index += 1

            # return loaded row number
            return index

    @staticmethod
    def load_initial_cc_supplier(in_file='TEC/cc-suppliers.csv'):
        """ Load cc location. """
        print("Start loading...")

        # delete existed objects
        models.InboundCCSupplierRate.objects.all().delete()

        # find csv file path
        with open(os.path.join(PERSISTENCE_DIR, in_file), encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            for row in reader:
                if index > 0:  # skip header
                    supplier_duns = row[0].strip()
                    supplier_name = row[1].strip()
                    pick_up_location = row[2].strip()
                    state = row[3].strip()
                    city = row[4].strip()
                    zip_code = row[5].strip()
                    kilometers = float(row[6].strip()) if row[6].strip() else None
                    rate = float(row[7].strip()) if row[7].strip() else None
                    cpc = float(row[8].strip()) if row[8].strip() else None

                    s = models.InboundCCSupplierRate(
                        supplier_duns=supplier_duns,
                        supplier_name=supplier_name,
                        pick_up_location=pick_up_location,
                        state=state,
                        city=city,
                        zip_code=zip_code,
                        kilometers=kilometers,
                        rate=rate,
                        cpc=cpc,
                    )

                    # save models
                    s.save()

                # print(index)
                index += 1

            # return loaded row number
            return index

    @staticmethod
    def load_initial_supplier_rate(in_file='TEC/supplier-rate.csv'):
        """ Load cc location. """
        print("Start loading...")

        # delete existed objects
        models.InboundSupplierRate.objects.all().delete()

        # find csv file path
        with open(os.path.join(PERSISTENCE_DIR, in_file), encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            # reverse mapping of base
            REV_BASE_CHOICE = dict()
            for _i, _s in models.BASE_CHOICE:
                if _i >= 0:  # exclude 3rd party
                    REV_BASE_CHOICE[_s] = _i

            for row in reader:
                if index >= 0:  # skip header
                    base = REV_BASE_CHOICE[row[0]]
                    pickup_location = row[1].strip() if row[1].strip() else None
                    supplier = row[2].strip() if row[2].strip() else None
                    forward_rate = float(row[3].strip()) if row[3].strip() else None
                    backward_rate = float(row[4].strip()) if row[4].strip() else None
                    manage_ratio = float(row[5].strip()[: -1]) * 0.01 if row[5].strip() else None
                    vmi_rate = float(row[6].strip()) if row[6].strip() else None
                    oneway_km = float(row[7].strip()) if row[7].strip() else None
                    address = row[8].strip() if row[8].strip() else None

                    s = models.InboundSupplierRate(
                        base=base,
                        pickup_location=pickup_location,
                        supplier=supplier,
                        forward_rate=forward_rate,
                        backward_rate=backward_rate,
                        manage_ratio=manage_ratio,
                        vmi_rate=vmi_rate,
                        oneway_km=oneway_km,
                        address=address
                    )

                    # save models
                    s.save()

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

    @staticmethod
    def load_initial_truck_rate(in_file='TEC/truck-rate.csv'):
        """ Load truck rate data into backend database. """
        print("Start loading...")

        # delete all existed records
        models.TruckRate.objects.all().delete()

        # find csv file path
        csv_path = os.path.join(PERSISTENCE_DIR, in_file)

        # reverse mapping of base
        REV_BASE_CN_NAME_CHOICE = dict()
        BASE_CN_NAME_ABBR = {
            'JQ': '上海',
            'WH': '武汉',
            'NS': '北盛',
            'DY': '东岳'
        }

        BASE_CHOICE = (
            (0, 'JQ'),
            (1, 'DY'),
            (3, 'NS'),
            (4, 'WH'),
            (-1, '3rd Party')
        )

        for _i, _s in BASE_CHOICE:
            if _i >= 0:  # exclude 3rd party
                REV_BASE_CN_NAME_CHOICE[BASE_CN_NAME_ABBR[_s]] = _i

        with open(csv_path, encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            for row in reader:
                if index > 0:  # skip header

                    name = row[0].strip()
                    cube = float(row[1].strip())
                    loading_ratio = float(row[2].strip())
                    capable_cube = float(row[3].strip())
                    avg_speed = float(row[4].strip())
                    load_time = float(row[5].strip())
                    oil_price = float(row[6].strip()) if row[6] != '无' else None
                    charter_price = float(row[7].strip()) if row[7].strip() else None
                    overdue_price = float(row[8].strip()) if row[8].strip() else None
                    rate_per_km = float(row[9].strip()) if row[9].strip() else None

                    base = REV_BASE_CN_NAME_CHOICE[name[0: 2]]

                    t = models.TruckRate(
                        name=name,

                        cube=cube,
                        loading_ratio=loading_ratio,
                        capable_cube=capable_cube,
                        avg_speed=avg_speed,
                        load_time=load_time,
                        oil_price=oil_price,
                        charter_price=charter_price,
                        overdue_price=overdue_price,
                        rate_per_km=rate_per_km,
                        base=base
                    )

                    # save models
                    t.save()

                # print(index)
                index += 1

        return index

    @staticmethod
    def load_initial_region_route_rate(in_file='TEC/region-route-rate.csv'):
        """ Load region/route rate data into backend database. """
        print("Start loading...")

        # delete all existed records
        models.RegionRouteRate.objects.all().delete()

        # find csv file path
        csv_path = os.path.join(PERSISTENCE_DIR, in_file)

        with open(csv_path, encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # row index
            index = 0

            BASE_CHOICE = (
                (0, 'JQ'),
                (1, 'DY'),
                (3, 'NS'),
                (4, 'WH'),
                (-1, '3rd Party')
            )

            for row in reader:
                if index > 0:  # skip header

                    related_base = None
                    for _i, _s in BASE_CHOICE:
                        if row[0].strip() == _s:
                            related_base = _i

                    parent_region = row[1].strip() if row[1].strip() else None
                    region_or_route = row[2].strip()
                    km = float(row[3].strip())
                    price_per_cube = float(row[4].strip())
                    reference = row[5].strip() if row[4].strip() else None

                    r = models.RegionRouteRate(
                        related_base=related_base,
                        region_or_route=region_or_route,
                        parent_region=parent_region,
                        km=km,
                        price_per_cube=price_per_cube,
                        reference=reference
                    )

                    # save models
                    r.save()

                # print(index)
                index += 1

        return index


class ParseArray:
    """ Parse two-dimensional array of excel. """

    @staticmethod
    def parse_tcs(matrix: list):
        """ Parse TCS data. """
        # tcs header
        TCS_HEADER = [
            {'r_offset': 0, 'ex_header': 'P/N', 'in_header': 'part_number'},
            {'r_offset': 0, 'ex_header': 'DUNS', 'in_header': 'duns'},
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

            # always create new tcs & package objects
            try:
                unsorted_tcs_object = models.UnsortedInboundTCS(part_number=lookup_value)
                params = dict()

                for dict_obj in TCS_HEADER[1:]:
                    if 'match_display' in dict_obj:
                        choice = getattr(unsorted_tcs_object, dict_obj['in_header'] + '_choice')

                        for int_val, str_val in choice:
                            if row[dict_obj['col']].strip().upper() == str_val.upper():
                                params[dict_obj['in_header']] = int_val
                                break

                    else:
                        params[dict_obj['in_header']] = row[dict_obj['col']]

                for attribute in params:
                    if params[attribute] == '':
                        params[attribute] = None
                    setattr(unsorted_tcs_object, attribute, params[attribute])

                unsorted_tcs_object.save()

            except Exception as e:
                print(e)

    @staticmethod
    def parse_buyer(matrix: list):
        """ Parse TCS data. """
        # buyer header
        BUYER_HEADER = [
            {'r_offset': 0, 'ex_header': '零件号', 'in_header': 'bom:part_number'},
            {'r_offset': 0, 'ex_header': '采购员', 'in_header': 'buyer'},
            {'r_offset': 0, 'ex_header': '运输模式', 'in_header': 'contract_incoterm'},
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

    @staticmethod
    def load_initial_unsorted_buyer(in_folder='buyer') -> int:
        """ Load sgm plant data into backend database. """
        print("Start loading...")

        # delete all existed records
        models.UnsortedInboundBuyer.objects.all().delete()

        # search directory
        search_dir = os.path.join(PERSISTENCE_DIR, in_folder)
        index = 0

        for file in os.listdir(search_dir):
            # row index
            index = 0

            with open(os.path.join(PERSISTENCE_DIR, in_folder, file), encoding='gbk') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')

                for row in reader:
                    if index > 3:  # skip header
                        part_number = row[0].strip() if row[0].strip() else None
                        part_name = row[1].strip() if row[1].strip() else None
                        duns = row[2].strip() if row[2].strip() else None
                        supplier_name = row[3].strip() if row[3].strip() else None
                        buyer = row[5].strip() if row[5].strip() else None
                        measure_unit = row[6].strip() if row[6].strip() else None
                        currency_unit = row[7].strip() if row[7].strip() else None

                        if row[8].strip() == '烟台东岳':
                            area = 1
                        elif row[8].strip() == '上海金桥':
                            area = 0
                        elif row[8].strip() == '沈阳北盛':
                            area = 3
                        elif row[8].strip() == '动力总成':
                            area = 10
                        else:
                            area = -1

                        inner_pkg_cost = float(row[9].strip()) if row[9].strip() else None
                        inner_pkg_owner = row[10].strip() if row[10].strip() else None
                        outer_pkg_cost = float(row[11].strip()) if row[11].strip() else None
                        outer_pkg_owner = row[12].strip() if row[12].strip() else None
                        carrier = row[13].strip() if row[13].strip() else None
                        transport_cost = float(row[14].strip()) if row[14].strip() else None
                        transport_mode = row[15].strip() if row[15].strip() else None

                        if row[16].strip() == '0':
                            whether_seq = False
                        elif row[16].strip() == '1':
                            whether_seq = True
                        else:
                            whether_seq = None

                        seq_cost = float(row[17].strip()) if row[17].strip() else None
                        location = row[18].strip() if row[18].strip() else None
                        bidderlist_no = row[19].strip() if row[19].strip() else None
                        project = row[20].strip() if row[20].strip() else None

                        if not part_name or not duns:
                            continue

                        t = models.UnsortedInboundBuyer(
                            part_number=part_number,
                            part_name=part_name,
                            duns=duns,
                            supplier_name=supplier_name,
                            buyer=buyer,
                            measure_unit=measure_unit,
                            currency_unit=currency_unit,
                            area=area,
                            inner_pkg_cost=inner_pkg_cost,
                            inner_pkg_owner=inner_pkg_owner,
                            outer_pkg_cost=outer_pkg_cost,
                            outer_pkg_owner=outer_pkg_owner,
                            carrier=carrier,
                            transport_cost=transport_cost,
                            transport_mode=transport_mode,
                            whether_seq=whether_seq,
                            seq_cost=seq_cost,
                            location=location,
                            bidderlist_no=bidderlist_no,
                            project=project,
                        )

                        # save models
                        t.save()

                    # print(index)
                    index += 1

        # return loaded row number
        return index

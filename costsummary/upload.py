from . import models
from django.http import HttpResponseRedirect
from django.urls import reverse

def load_initial_tec_num(matrix: list):
    """ Load sgm plant data into backend database. """
    print("Start loading...")

    # delete all existed records
    models.TecCore.objects.all().delete()
        # row index
    index = len(matrix)
    for row in matrix[1:]:
        tec_id = row[0]
        common_part_name = row[1].strip()
        mgo = row[2].strip()

        t = models.TecCore(
            tec_id=tec_id,
            common_part_name=common_part_name.upper(),  # upper case
            mgo_part_name_list=mgo.upper()
        )

        # save models
        t.save()

    # return loaded row number
    return index


def load_initial_packing_folding_rate(matrix: list):
    """ Load sgm plant data into backend database. """
    print("Start loading...")

    # delete all existed records
    models.PackingFoldingRate.objects.all().delete()

    # row index
    index = len(matrix)
    for row in matrix[1:]:
        packing_type = row[0].strip()
        folding_rate = row[1]

        t = models.PackingFoldingRate(
            packing_type=packing_type.upper(),
            folding_rate=folding_rate  # upper case
        )

        # save models
        t.save()

    # return loaded row number
    return index


def load_initial_air_freight_rate(matrix: list):
    """ Load sgm plant data into backend database. """
    print("Start loading...")

    # delete all existed records
    models.AirFreightRate.objects.all().delete()

    # row index
    index = len(matrix)
    for row in matrix[1:]:
        country = row[0].strip()
        base = row[1].strip()
        rate = row[2]
        danger_rate = row[3]
        t = models.AirFreightRate(
            country=country,
            base=base,  
            rate=rate,
            danger_rate=danger_rate                  
        )

        # save models
        t.save()

    # return loaded row number
    return index


def load_initial_wh_cube_price(matrix: list):
    """ Load sgm plant data into backend database. """
    print("Start loading...")

    # delete all existed records
    models.WhCubePrice.objects.all().delete()

    # row index
    index = 0
    for row in matrix[1:]:
        km = row[0]
        cube_price = row[1]

        t = models.WhCubePrice(
            km=km,
            cube_price=cube_price 
        )

        # save models
        t.save()
    # return loaded row number
    return index


def load_initial_nl_mapping(matrix: list):
    """ Generate nominal label mapping according to book, plant and model. """
    print("Start loading...")

    # delete existed objects
    # models.NominalLabelMapping.objects.all().delete()

    for row in matrix[1:]:
        book = row[0].strip()
        plant_code = row[1].strip()
        model = row[2].strip()
        value = row[3]

        match_object = models.NominalLabelMapping.objects.filter(
                model=model,
                value=value).first()
        if not match_object:
            match_object =  models.NominalLabelMapping(
                model=model,
                value=value
            )
        setattr(match_object, 'book', book)
        setattr(match_object, 'plant_code', plant_code)  
        # save models
        match_object.save()


def load_initial_os_rate(matrix: list):
    """ Load initial oversea rate. """
    print("Start loading...")

    # delete existed objects
    models.InboundOverseaRate.objects.all().delete()

    # reverse mapping of base
    REV_BASE_CHOICE = dict()
    for _i, _s in models.BASE_CHOICE:
        if _i >= 0:  # exclude 3rd party
            REV_BASE_CHOICE[_s] = _i

    for row in matrix[1:]:
        region = row[0].strip().upper()
        base = REV_BASE_CHOICE[row[1].strip().upper()]
        cc = row[2].strip().upper()
        export_harbor = row[3].strip().upper()
        definition_harbor = row[4].strip().upper()
        os_dm_rate = float(row[5]) if row[5] else None
        cc_rate = float(row[6]) if row[6] else None
        euro_doc_rate = float(row[7]) if row[7] else None
        os_40h_rate = float(row[8]) if row[8] else None
        os_40h_danger_rate = float(row[9]) if row[9] else None
        inter_40h_rate = float(row[10]) if row[10] else None
        inter_40h_danger_rate = float(row[11]) if row[11] else None
        dm_40h_rate = float(row[12]) if row[12] else None
        dm_40h_danger_rate = float(row[13]) if row[13] else None
        delegate = float(row[14]) if row[14] else None
        delegate_danger = float(row[15]) if row[15] else None
        vol_40h = float(row[16]) if row[16] else None
        load_rate = float(row[17]) if row[17] else None
        cpc = float(row[18]) if row[18] else None
        cpc_danger = float(row[19]) if row[19] else None

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


def load_initial_cc_location(matrix: list):
    """ Load cc location. """
    print("Start loading...")

    # delete existed objects
    models.InboundCcLocations.objects.all().delete()

    for row in matrix[1:]:
        cc_group = int(row[0])
        cn_location_name = row[1].strip()
        en_location_name = row[2].strip().upper()
        currency_unit = int(row[3])
        per_cbm = float(row[4]) if row[4] else None
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

def load_initial_cc_danger(matrix: list):
    """ Load cc location. """
    print("Start loading...")

    # delete existed objects
    models.InboundDangerPackage.objects.all().delete()

    for row in matrix[1:]:
        from_to_type = int(row[0])
        from_one = row[1].strip().upper()
        to_one = row[2].strip().upper()
        standard = float(row[3]) if row[3] else None
        danger = float(row[4]) if row[4] else None

        d = models.InboundDangerPackage(
            from_to_type=from_to_type,
            from_one=from_one,
            to_one=to_one,
            standard=standard,
            danger=danger,
        )

        # save models
        d.save()

def load_initial_cc_supplier(matrix: list):
    """ Load cc location. """
    print("Start loading...")

    # delete existed objects
    models.InboundCCSupplierRate.objects.all().delete()

    for row in matrix[1:]:
        supplier_duns = row[0]
        supplier_name = row[1].strip()
        pick_up_location = row[2].strip()
        state = row[3].strip()
        city = row[4].strip()
        zip_code = row[5]
        kilometers = float(row[6]) if row[6] else None
        rate = float(row[7]) if row[7] else None
        cpc = float(row[8]) if row[8] else None

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



def load_initial_supplier_rate(matrix: list):
    """ Load cc location. """
    print("Start loading...")

    # delete existed objects
    models.InboundSupplierRate.objects.all().delete()
    # reverse mapping of base
    REV_BASE_CHOICE = dict()
    for _i, _s in models.BASE_CHOICE:
        if _i >= 0:  # exclude 3rd party
            REV_BASE_CHOICE[_s] = _i
    # row index
    for row in matrix[1:]:
        base = REV_BASE_CHOICE[row[0]]
        pickup_location = row[1].strip() if row[1].strip() else None
        supplier = row[2].strip() if row[2].strip() else None
        forward_rate = float(row[3]) if row[3] else None
        backward_rate = float(row[4]) if row[4] else None
        manage_ratio = float(row[5]) if row[5] else None
        vmi_rate = float(row[6]) if row[6] else None
        oneway_km = float(row[7]) if row[7] else None

        s = models.InboundSupplierRate(
            base=base,
            pickup_location=pickup_location,
            supplier=supplier,
            forward_rate=forward_rate,
            backward_rate=backward_rate,
            manage_ratio=manage_ratio,
            vmi_rate=vmi_rate,
            oneway_km=oneway_km,
        )

        # save models
        s.save()


def load_initial_distance(matrix: list):
    print("Start loading...")

    # delete all existed records
    models.Supplier.objects.all().delete()
    models.SupplierDistance.objects.all().delete()

    # parse distance and comment from original data like '804（烟大线）'
    def parse_distance(distance_cell: str) -> tuple:
        # blank cell
        if not distance_cell:
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


    # reverse mapping of base
    REV_BASE_CHOICE = dict()
    for _i, _s in models.BASE_CHOICE:
        if _i >= 0:  # exclude 3rd party
            REV_BASE_CHOICE[_s] = _i

    for row in matrix[1:]:
        if not row[3]:  # primary key is the 4-th column (the duns)
            break

        original_source = row[0].strip() if row[0].strip() else None

        row_1 = row[1].strip()
        if row_1:
            if row_1 == 'Y' or row_1 == 'y':
                is_mono_address = True
            elif row_1 == 'N' or row_1 == 'n':
                is_mono_address = False
            else:
                # print(row_1)
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
                # print(row_2)
                raise Exception
        else:
            is_promised_address = None

        duns = row[3]
        name = row[4].strip()
        address = row[5].strip()

        post_code = row[6]
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
        jq = parse_distance(row[10])
        dy = parse_distance(row[11])
        ns = parse_distance(row[12])
        wh = parse_distance(row[13])

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


def load_initial_truck_rate(matrix: list):
    """ Load truck rate data into backend database. """
    print("Start loading...")

    # delete all existed records
    models.TruckRate.objects.all().delete()

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

    for row in matrix[1:]:
        name = row[0].strip()
        cube = float(row[1])
        loading_ratio = float(row[2])
        capable_cube = float(row[3])
        avg_speed = float(row[4])
        load_time = float(row[5])
        oil_price = float(row[6]) if row[6] else None
        charter_price = float(row[7]) if row[7] else None
        overdue_price = float(row[8]) if row[8] else None
        rate_per_km = float(row[9]) if row[9] else None

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


def load_initial_region_route_rate(matrix: list):
    """ Load region/route rate data into backend database. """
    print("Start loading...")

    # delete all existed records
    models.RegionRouteRate.objects.all().delete()

    BASE_CHOICE = (
        (0, 'JQ'),
        (1, 'DY'),
        (3, 'NS'),
        (4, 'WH'),
        (-1, '3rd Party')
    )

    for row in matrix[1:]:
        related_base = None
        for _i, _s in BASE_CHOICE:
            if row[1].strip() == _s:
                related_base = _i

        parent_region = row[2].strip() if row[2].strip() else None
        region_or_route = row[0].strip()
        km = float(row[3])
        price_per_cube = float(row[4])
        reference = row[5].strip() #if row[5].strip() else None

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


# 上传新车车型级别报表
def load_new_model_statistic(matrix: list):
    """ Load truck rate data into backend database. """
    print("Start loading...")

    for row in matrix[1:]:
        base = row[0].strip()
        plant_code = row[1].strip()
        value = row[2]
        model_year = int(row[3])
        volume = float(row[4])
        inbound_ttl_veh = float(row[5])
        import_ib = float(row[6])
        dom_ddp_ib = float(row[7])
        dom_fca_ib = float(row[8])
        production = float(row[9])
        dom_volume = float(row[10])
        dom_rate = float(row[11])
        local_volume = float(row[12])
        local_rate = float(row[13])
        park_volume = float(row[14])
        park_rate = float(row[15])

        match = models.NewModelStatistic.objects.filter(base=base,plant_code=plant_code, value=value,model_year=model_year).first()

        if not match:
            match = models.NewModelStatistic(
                base=base,
                plant_code=plant_code, 
                value=value,
                model_year=model_year
                )
        setattr(match, 'volume', volume)
        setattr(match, 'inbound_ttl_veh', inbound_ttl_veh)
        setattr(match, 'import_ib', import_ib)
        setattr(match, 'dom_ddp_ib', dom_ddp_ib)
        setattr(match, 'dom_fca_ib', dom_fca_ib)
        setattr(match, 'production', production)
        setattr(match, 'dom_volume', dom_volume)
        setattr(match, 'dom_rate', dom_rate)
        setattr(match, 'local_volume', local_volume)
        setattr(match, 'local_rate', local_rate)
        setattr(match, 'park_volume', park_volume)
        setattr(match, 'park_rate', park_rate)
        match.save()





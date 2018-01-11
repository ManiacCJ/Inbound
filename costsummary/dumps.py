import os
import csv
from django.db import IntegrityError
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
    def load_initial_tec_num(in_file='TEC/tec-num.csv') -> int:
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

                    t = models.TecCore(
                        tec_id=tec_id,
                        common_part_name=common_part_name.upper(),  # upper case
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

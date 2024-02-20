import argparse
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from strAPI.repeats.models import Repeat, Gene, TRPanel, AlleleSequence
import math
import os

def round_sf(number):
    if number == 0:
        return 0.0
    else:
        #using 2 because we decided on 2 sf
        precision = 2 - int(math.floor(math.log10(abs(number)))) - 1
        return round(number, precision)



def connection_setup(db_path):
    engine = create_engine(db_path, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    return engine, session

import argparse
import os
import math
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from strAPI.repeats.models import Repeat, Gene, TRPanel, AlleleSequence

def round_sf(number):
    if number == 0:
        return 0.0
    else:
        # Using 2 because we decided on 2 significant figures
        precision = 2 - int(math.floor(math.log10(abs(number)))) - 1
        return round(number, precision)

def connection_setup(db_path):
    engine = create_engine(db_path, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    return engine, session

def main():
    default_path = "postgresql://webstr:webstr@localhost:5432/strdb"
    parser = argparse.ArgumentParser(description="Insert data into PostgreSQL database")
    parser.add_argument("--db_path", type=str, default=default_path, help="PostgreSQL connection URL")
    parser.add_argument("--directory", type=str, default=".", help="Directory containing input files")
    args = parser.parse_args()
    engine, session = connection_setup(args.db_path)

    # get chr files from chr dir
    files = os.listdir(args.directory)
    # Sort from 1 -22
    sorted_files = sorted(files, key=lambda x: int(x.split(".")[0][3:]))

    # run all chr files
    for filename in sorted_files:
        filepath = os.path.join(args.directory, filename)
        if not filename.endswith(".tab"):
            continue  # ensure only chr files processed 

        print(f"-----Processing {filename}-----")

        with open(filepath, "r") as file:
            next(file)  # Skip the header
            
            pop_indices = {"AFR": 3, "AMR": 4, "EAS": 5, "EUR": 6, "SAS": 7}
            
            for line in file:
                columns = line.strip().split()

                try:
                    db_repeat = session.query(Repeat).filter(
                        Repeat.source == 'EnsembleTR',
                        Repeat.start == int(columns[1]),
                        Repeat.end.between(int(columns[2]) - 2, int(columns[2]) + 2),
                        Repeat.chr == columns[0]
                    ).one()
                    print("Database Repeat:", db_repeat)

                except MultipleResultsFound as ex:
                    error_message = f"Multiple results found for chr: {columns[0]}:{columns[1]}-{columns[2]}"
                    print(error_message)
                    continue  

                except NoResultFound as ex:
                    error_message = f"No matching record found for chr: {columns[0]}:{columns[1]}-{columns[2]}"
                    print(error_message)
                    continue  

                for pop in ["AFR", "AMR", "EAS", "EUR", "SAS"]:
                    popdata = columns[pop_indices[pop]] 
                    popdata_items = popdata.split(",")
                    total = 0
                    if len(popdata_items) >= 2:
                        total = np.sum([int(item.split(":")[1]) for item in popdata.split(",")])

                    if len(popdata_items) < 2:
                        continue

                    alleles = popdata.split(",")
                    for a in alleles:
                        allele_items = a.split(":")
                        if len(allele_items) >= 2:
                            aseq = allele_items[0]
                            acount = int(allele_items[1])
                            freq = round_sf(acount/total)
                            db_seq = AlleleSequence(
                                repeat_id=db_repeat.id,
                                population=pop, 
                                n_effective=db_repeat.n_effective,
                                frequency=freq,
                                num_called=acount,
                                sequence=aseq
                            )
                            db_repeat.allseq.append(db_seq)
                        else:
                            continue
        print(f"-----Processing {filename}-----")

    session.commit()
    session.close()
    engine.dispose()
    print("Data inserted successfully")

if __name__ == "__main__":
    main()



import argparse
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from strAPI.repeats.models import Repeat, Gene, TRPanel, AlleleSequence
import math

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

def main():
    default_path = "postgresql://webstr:webstr@localhost:5432/strdb"
    parser = argparse.ArgumentParser(description="Insert data into PostgreSQL database")
    parser.add_argument("--db_path", type=str, default=default_path, help="PostgreSQL connection URL")
    args = parser.parse_args()
    engine, session = connection_setup(args.db_path)

    # Open and read the text file, then insert data row by row
    with open("chr11_test2.tab", "r") as file:
        # Skip the header
        next(file) 
        
        pop_indices = {"AFR":3, "AMR":4, "EAS":5, "EUR":6, "SAS":7}
        
        for line in file:
            # Split the line into columns, assuming values are separated by spaces 
            columns = line.strip().split()

            try:
                # Extract repeat id
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

            # now that repeat id has been extracted
            for pop in ["AFR", "AMR", "EAS", "EUR", "SAS"]:
                # extract data for this population
                popdata = columns[pop_indices[pop]] 
                popdata_items = popdata.split(",")
                

                total = 0
                #to avoid errors for populations w/ no data
                if len(popdata_items) >=2:
                    # first get count for freqs
                    total = np.sum([int(item.split(":")[1]) for item in popdata.split(",")])
                
                #should we set to 0 or skip it?
                if len(popdata_items) <2:
                    continue



                # parse info and make one db entry per allele
                alleles = popdata.split(",")
                
                for a in alleles:
                    allele_items = a.split(":")

                    if len(allele_items) >= 2:
                        aseq = allele_items[0]
                        acount = int(allele_items[1])
                        freq = round_sf(acount/total)

                        # enter into db
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

    # Commit the changes and close the session
    session.commit()
    session.close()
    engine.dispose()

    print("Data inserted successfully")

if __name__ == "__main__":
    main()


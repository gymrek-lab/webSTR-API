import argparse
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from strAPI.repeats.models import Repeat, Gene, TRPanel, AlleleSequence
import math
import os
from tqdm import tqdm


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


def process_file(filepath, session, error_log_file, skipped_lines_file):
    with open(filepath, "r") as file:
        next(file)

        pop_indices = {"AFR": 3, "AMR": 4, "EAS": 5, "EUR": 6, "SAS": 7}
        total_lines = sum(1 for line in file)  # Count total lines in the file

        # Reset file pointer to the beginning of the file
        file.seek(0)

        # Create tqdm progress bar for the current file
        progress_bar = tqdm(total=total_lines, desc=f"Processing {os.path.basename(filepath)}", unit="line")

        for line_number, line in enumerate(file, start=1):
            progress_bar.update(1)  # Increment progress bar by 1 for each line processed
            columns = line.strip().split()

            try:
                #print("Columns:", columns)  
                db_repeat = session.query(Repeat).filter(
                    Repeat.source == 'EnsembleTR',
                    Repeat.start == int(columns[1]),
                    Repeat.end.between(int(columns[2]) - 2, int(columns[2]) + 2),
                    Repeat.chr == columns[0]
                ).one()
                # print("Database Repeat:", db_repeat)

            except ValueError as ex:
                # Handle the case where the start column cannot be converted to an integer
                error_message = f"Invalid value for start column: {ex} with line contents: {columns}"
                #print(error_message)
                error_log_file.write(error_message + '\n')  # Write error message to log file
                continue
            
            except IndexError as ex:
                # Handle the case where there are not enough columns in the line
                error_message = f"Not enough columns in line: {line}"
                #print(error_message)
                error_log_file.write(error_message + '\n')  # Write error message to log file
                continue

            except MultipleResultsFound as ex:
                error_message = f"Multiple results found for chr: {columns[0]}:{columns[1]}-{columns[2]}"
                #print(error_message)
                error_log_file.write(error_message + '\n')  # Write error message to log file
                continue

            except NoResultFound as ex:
                error_message = f"No matching record found for chr: {columns[0]}:{columns[1]}-{columns[2]}"
                #print(error_message)
                error_log_file.write(error_message + '\n')  # Write error message to log file
                continue

            for pop in ["AFR", "AMR", "EAS", "EUR", "SAS"]:
                popdata = columns[pop_indices[pop]]
                popdata_items = popdata.split(",")
                total = 0


                ###test###
                #print("popdata:", popdata) 
                #print("popdata_items:", popdata_items)  
                #print("Number of items in popdata_items:", len(popdata_items))  



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
                        freq = round_sf(acount / total)
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
                        skipped_lines_file.write(f"Skipped line else condition of allele loop {line_number}: {line}\n")
                        continue

        # Close the tqdm progress bar
        progress_bar.close()



def main():
    default_path = "postgresql://webstr:webstr@localhost:5432/strdb"
    default_error_log = "error_chr4.log"
    default_skipped_lines_file = "skipped_lines_chr4.txt"
    default_file ="/gymreklab-tscc/creeve/chr/chr4.tab"
    parser = argparse.ArgumentParser(description="Insert data into PostgreSQL database")
    parser.add_argument("--db_path", type=str, default=default_path, help="PostgreSQL connection URL")
    parser.add_argument("--file", type=str, default=default_file,help="File to process")
    parser.add_argument("--error_log", type=str, default=default_error_log, help="Path to error log file")
    parser.add_argument("--skipped_lines_file", type=str, default=default_skipped_lines_file, help="Path to skipped lines file")
    
    args = parser.parse_args()
    engine, session = connection_setup(args.db_path)

    with open(args.error_log, 'w') as error_log_file, \
         open(args.skipped_lines_file, 'w') as skipped_lines_file:  
        process_file(args.file, session, error_log_file, skipped_lines_file)  

    session.commit()
    session.close()
    engine.dispose()
    print("Data inserted successfully")

if __name__ == "__main__":
    main()

from operator import index

import re
import os

import pandas as pd
import numpy as np

from datetime import datetime

# Get today's date
today = datetime.today()


########################################################################################################################

def remove_duplicates(df: pd.DataFrame, search_column: str, file_name: str, search_keys: list = None):
    """
    Method for analyzes an input df for duplicates and if any are found they get stored
    to file. The methods also return a non duplicated version of the inputted dataframe

    Parameters
    ----------
    df                      : pd.DataFrame
                              dataframe to analyze for duplicates
    search_column           : str
                              name of column to search for duplicates
    file_name               : str
                              filename of duplicate
    search_keys             : list
                              list of values to extract from df, assuming the values
                              in list are duplicates

    Returns
    -------
    out                     : list, df
                              a list of duplicates found, and a df with non duplicates

    NB : all duplicate found gets saved to file in a duplicates dir

    """

    if not file_name.endswith('.xlsx'):
        raise ValueError("invalid file format, only possible '.xlsx'")

    duplicates_dir = os.path.dirname(__file__) + '/data/duplicates/'

    if not os.path.exists(duplicates_dir):
        os.makedirs(duplicates_dir)

    non_duplicates_df = df[~df.duplicated(subset=search_column, keep=False)]

    if search_keys is None:
        duplicates = df[df.duplicated(subset=search_column, keep=False)]
        duplicates.to_excel(duplicates_dir + file_name, index=False)

        return duplicates[search_column].tolist(), non_duplicates_df
    else:
        duplicates = df[df[search_column].isin(search_keys)]
        duplicates.to_excel(duplicates_dir + file_name, index=False)

        return duplicates[search_column].tolist(), non_duplicates_df


data_file = os.path.dirname(__file__) + '/nav/data/Datagrunnlag.xlsx'

members = pd.read_excel(data_file, sheet_name='Medlemmer')
membership = pd.read_excel(data_file, sheet_name='Kontingent')
payment = pd.read_excel(data_file, sheet_name='Betalinger')

duplicate_members_list, members = remove_duplicates(members, 'Medlemsnummer',
                                                    'duplikate_medlemmer.xlsx')
duplicate_payment_list, payment = remove_duplicates(payment, 'Medlemsnummer',
                                                    file_name='duplikate_betalinger.xlsx',
                                                    search_keys=duplicate_members_list)


########################################################################################################################

def detect_and_replace_missing_info(df: pd.DataFrame):
    """
     A method for detecting missing information (i.e., missing or NaN values) in a DataFrame and replacing them with -1
    """
    # Sjekk om det finnes manglende verdier i datasettet før vi endrer
    if df.isnull().values.any():
        print("Det finnes manglende verdier i datasettet.")
        print("Antall manglende verdier per kolonne:")
        print(df.isnull().sum())  # Vis antall manglende verdier per kolonne

        # Erstatt manglende verdier (NaN) med -1
        df_filled = df.fillna(-1)
        print("\nManglende verdier er nå erstattet med -1.")
    else:
        print("Ingen manglende verdier i datasettet.")
        df_filled = df  # Hvis det ikke er noen manglende verdier, returner original DataFrame

    # Finn rader som inneholder manglende verdier (nå erstattet med -1)
    manglende_verdier = df_filled[df_filled.isnull().any(axis=1)]

    if not manglende_verdier.empty:
        print("Rader med manglende verdier (som nå er -1):")
        print(manglende_verdier)
    else:
        print("Ingen rader med manglende verdier etter erstatning.")

    # Returner den fylte DataFrame (som en mulighet for videre behandling) og foreta en siste vask av kolonne navn
    df_filled.columns = df_filled.columns.str.replace(' ', '', regex=False).str.capitalize()

    for col in df_filled.columns:
        if df_filled[col].dtype == 'object':  # Check if the column contains string values
            df_filled[col] = df_filled[col].str.replace(' ', '').str.capitalize()

    return df_filled


# Erstatter manglende verdier med -1
members = detect_and_replace_missing_info(members)
membership = detect_and_replace_missing_info(membership)
payment = detect_and_replace_missing_info(payment)

########################################################################################################################

historic_payment_with_member_data = pd.merge(payment, members, how='left',
                                             on=["Medlemsnummer"])


########################################################################################################################

def decide_member_age(df: pd.DataFrame, date_column: str, new_column_name: str):
    df[new_column_name] = pd.to_datetime(df[date_column], format="%d.%m.%Y", errors='coerce')
    df[new_column_name] = ((today - df[new_column_name]).dt.days // 365).fillna(-1).astype(int)


decide_member_age(historic_payment_with_member_data, 'Fødselsdato', 'Alder')


def decide_range(age_group: str):
    """
    Splits an age range string into min and max values.
    Handles ranges with '-' and '+'.

    """
    if '-' in age_group:
        start, end = map(int, age_group.split('-'))
    elif '+' in age_group:
        start = list(map(int, re.findall(r'\d+', age_group)))[0] + 1
        end = np.inf  # Using NumPy's infinity for no upper limit
    else:
        raise ValueError(f"Unexpected format: {age_group}")
    return start, end


membership[['MinAlder', 'MaxAlder']] = membership['Aldersgruppe'].apply(
    lambda x: pd.Series(decide_range(x))
)

historic_payment_with_member_data.rename(columns={'Medlemstype': 'MedlemstypeGammel'}, inplace=True)

historic_payment_with_member_data = historic_payment_with_member_data.merge(membership, on="Periode",
                                                                            how="left").query(
    "Alder >= MinAlder and Alder <= MaxAlder")
historic_payment_with_member_data.rename(columns={'Medlemstype': 'MedlemstypeNy'}, inplace=True)

historic_payment_with_member_data['FeilMedlemstype'] = historic_payment_with_member_data['MedlemstypeGammel'] != \
                                                       historic_payment_with_member_data['MedlemstypeNy']

historic_payment_with_member_data['FeilBetaling'] = historic_payment_with_member_data['Beløp'] != \
                                                    historic_payment_with_member_data['Kontingent']

historic_payment_with_member_data.to_excel('results.xlsx', index=False)

# def is_within_range(number, lower_bound, upper_bound):
#     return lower_bound <= number <= upper_bound
# def correct_membership(df: pd.DataFrame):


# print(membership.columns.to_list())


########################################################################################################################
# result_1 = pd.merge(historic_payment_with_member_data, membership, how='left', on=["Periode", "Medlemstype"])
# result_1.columns = result_1.columns.str.strip()
#
# new_order = ['Innbetalt_dato', 'Periode', 'Medlemsnummer', 'Fødselsdato', 'Medlemstype', 'Aldersgruppe', 'Intervall',
#              'Alder', 'Fornavn', 'Etternavn', 'Kjønn', 'Gateadresse', 'Postnummer', 'Poststed', 'Kontingent', 'Beløp']
# result_1 = result_1[new_order]
# result_1['Membership Assessment'] = result_1['Alder'].apply(is_within_range(result_1['Intervall'].str.strip()))
########################################################################################################################
# result_1['Intervall'] = result_1['Intervall'].str.strip().astype(str)
# result_1[['Fra', 'Til']] = result_1['Intervall'].str.extract(r'\((\d+),\s*(\d+)\)')
# print(result_1['Intervall'].str.extract(r'\((\d+),\s*(\d+)\)').head())
# Konverter 'Fra' og 'Til' til numeriske verdier
# result_1['Fra'] = pd.to_numeric(result_1['Fra'])
# result_1['Til'] = pd.to_numeric(result_1['Til'])
# print(result_1['Fra'].head())
# result_1.to_excel('result.xlsx', index=False)
# print(2024 - dt1_new['Ny Fødselsdato'].dt.year)
# medlemmer['Medlemstype'] = medlemmer['Medlemstype'].str.lower()
# kontingent['Medlemstype'] = kontingent['Medlemstype'].str.lower()
# print("************************************************************")

# print("************************************************************")

# print(result_0.loc[:])
# print("************************************************************")

#
# result_1 = pd.merge(result_0, kontingent, how='left', on=["Periode", "Medlemstype"])
#
# print(result_1.head(2).to_dict())

# result_1.to_excel('dt_result.xlsx', index=False)

# print(result_1.loc[:])


# dt1_new['Aldersfo]rskjell'] = 2024 - dt1_new['Ny Fødselsdato'].dt.year
# print(dt1_new.loc[:, ["Fødselsdato", "Ny Fødselsdato", 'Aldersforskjell', 'Medlemstype']])
# dt1_new['Korrekt medlemstype'] = np.where(dt1_new['Medlemstype'] == dt2['Aldersgruppe'], 'Yes', 'No')
# dt1_new['Alderkrav'] = dt1_new['aldersforskjell'].apply(lambda x: ' Short' if x<165 else('Average' if x<185 else 'Tall'))

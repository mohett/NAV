import pandas as pd
import numpy as np
import os
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


data_file = os.path.dirname(__file__) + '/data/Datagrunnlag.xlsx'

members = pd.read_excel(data_file, sheet_name='Medlemmer')
membership = pd.read_excel(data_file, sheet_name='Kontingent ')
payment = pd.read_excel(data_file, sheet_name='Betalinger')

duplicate_members_list, non_duplicate_members_df = remove_duplicates(members, 'Medlemsnummer',
                                                                     'duplikate_medlemmer.xlsx')
duplicate_payment_list, non_duplicate_payment_df = remove_duplicates(payment, 'Medlemsnummer',
                                                                     file_name='duplikate_betalinger.xlsx',
                                                                     search_keys=duplicate_members_list)

# result_0['Periode'] = result_0['Innbetalt_dato'].dt.year
########################################################################################################################
result_0 = pd.merge(non_duplicate_payment_df, non_duplicate_members_df, how='left', on=["Medlemsnummer"])
result_0.columns = result_0.columns.str.strip()
result_0["Medlemstype"] = result_0["Medlemstype"].str.strip().str.capitalize()
membership["Medlemstype"] = membership["Medlemstype"].str.strip().str.capitalize()
result_1 = pd.merge(result_0, membership, how='left', on=["Periode", "Medlemstype"])
result_1.columns = result_1.columns.str.strip()
########################################################################################################################

new_order = ['Innbetalt_dato', 'Periode', 'Medlemsnummer', 'Medlemstype', 'Fødselsdato', 'Aldersgruppe', 'Fornavn',
             'Etternavn',
             'Kjønn', 'Gateadresse', 'Postnummer', 'Poststed', 'Kontingent', 'Beløp']
result_1 = result_1[new_order]
print(result_1.columns.to_list())


########################################################################################################################
def decide_member_age(df: pd.DataFrame, date_column: str, new_column_name: str):
    df[new_column_name] = pd.to_datetime(df[date_column], format="%d.%m.%Y", errors='coerce')
    df[new_column_name] = ((today - df[new_column_name]).dt.days // 365).fillna(-1).astype(int)
    # df[new_column_name] = df[new_column_name].dt.year

def decide_membership(df: pd.DataFrame, df1: pd.DataFrame):
    df1['Kontingent']


decide_member_age(result_0, 'Fødselsdato', 'Alder')

result_0.to_csv('dt_result.csv', index=False)

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

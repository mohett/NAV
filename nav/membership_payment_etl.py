from operator import index
import re
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Get today's date
today = datetime.today()

#Read data file and data sheets
data_file = os.path.dirname(__file__) + '/data/Datagrunnlag.xlsx'
members = pd.read_excel(data_file, sheet_name='Medlemmer')
membership = pd.read_excel(data_file, sheet_name='Kontingent')
payment = pd.read_excel(data_file, sheet_name='Betalinger')

########################################################################################################################
def remove_duplicates(df: pd.DataFrame, search_column: str, file_name: str, search_keys: list = None):
    """
    Method for analyzes an input df for duplicates and if any are found they get stored
    to file. The methods also return a non duplicated version of the inputted dataframe

    Args:
        df (pd.DataFrame): The input DataFrame to process.
        search_column (str): The column to search for duplicates.
        file_name (str): The file name to save duplicate data to (must end with '.xlsx').
        search_keys (list, optional): Specific keys to filter duplicates (default: None).

    Returns:
        list: A list of duplicate values in the search column.
        pd.DataFrame: A DataFrame with duplicates removed.
    """
    if not file_name.endswith('.xlsx'):
        raise ValueError("invalid file format, only possible '.xlsx'")

    # Define the directory where duplicate files will be stored
    data_wash_dir = os.path.dirname(__file__) + '/data/datavask/'

    if not os.path.exists(data_wash_dir):
        os.makedirs(data_wash_dir)

    # Filter rows that are NOT duplicates based on the specified column
    non_duplicates_df = df[~df.duplicated(subset=search_column, keep=False)]

    if search_keys is None: # If no specific keys are provided
        # Filter rows that are duplicates based on the specified column
        duplicates = df[df.duplicated(subset=search_column, keep=False)]
        duplicates.to_excel(data_wash_dir + file_name, index=False)

        return duplicates[search_column].tolist(), non_duplicates_df
    else:
        # If specific keys are provided
        # Filter rows where the column's values match the search keys
        duplicates = df[df[search_column].isin(search_keys)]
        duplicates.to_excel(data_wash_dir + file_name, index=False)

        return duplicates[search_column].tolist(), non_duplicates_df


# Find and process duplicate members based on 'Medlemsnummer'
duplicate_members_list, members = remove_duplicates(members, 'Medlemsnummer',
                                                    'duplikate_medlemmer.xlsx')

# Find and process duplicate payments based on 'Medlemsnummer'
duplicate_payment_list, payment = remove_duplicates(payment, 'Medlemsnummer',
                                                    file_name='duplikate_betalinger.xlsx',
                                                    search_keys=duplicate_members_list)

########################################################################################################################


def wrong_birthday(df: pd.DataFrame, date_column: str, file_name: str):
    """
    A method for detecting missing information (i.e., missing or NaN values) in a DataFrame and replacing them with -1.

     Args:
        df (pd.DataFrame): Input DataFrame to process.
        date_column (str): The column containing dates to validate.
        file_name (str): The file name to save invalid date records (must end with '.xlsx').

    Returns:
        pd.DataFrame: The DataFrame with invalid dates removed.
        Additionally, checks if the date is valid (not in the future).
    """
    if not file_name.endswith('.xlsx'):
        raise ValueError("invalid file format, only possible '.xlsx'")

    data_wash_dir = os.path.dirname(__file__) + '/data/datavask/'

    if not os.path.exists(data_wash_dir):
        os.makedirs(data_wash_dir)

    try:
        # Convert the date column to datetime, coercing invalid values to NaT (Not a Time)
        df[date_column] = pd.to_datetime(df[date_column], format='%d.%m.%Y', errors='coerce')

        # Identify invalid dates (NaT or dates in the future)
        invalid_dates = df[df[date_column].isnull() | (df[date_column] > datetime.now())]
        # Remove rows with invalid dates from the original DataFrame
        df = df[~df[date_column].isin(invalid_dates[date_column])]

        # If there are invalid dates, save them to an Excel file
        if not invalid_dates.empty:
            invalid_dates.to_excel(data_wash_dir + file_name, index=False)

        # Return the cleaned DataFrame with valid dates only
        return df
    except Exception as e:
        print(f"Feil ved behandling av dato: {e}")

# Clean the 'members' DataFrame by validating the 'Fødselsdato' (birthdate) column
members = wrong_birthday(members, 'Fødselsdato', 'invalid_birthdays.xlsx')

########################################################################################################################
def detect_and_replace_missing_info(df: pd.DataFrame):
    """
     A method for detecting missing information (i.e., missing or NaN values) in a DataFrame and replacing them with -1
     Also standardizes column names and string values by removing extra spaces and capitalizing them.

    Args:
        df (pd.DataFrame): The input DataFrame to process.

    Returns:
        pd.DataFrame: The processed DataFrame with missing values replaced and standardized formatting.
    """
    # Check if there are any missing (NaN) values in the DataFrame
    if df.isnull().values.any():
        # Replace all NaN values with -1 if any missing values are detected
        df_filled = df.fillna(-1)
    else:
        df_filled = df

    # Standardize column names: remove spaces and capitalize each name
    df_filled.columns = df_filled.columns.str.replace(' ', '', regex=False).str.capitalize()

    for col in df_filled.columns:
        if df_filled[col].dtype == 'object':  #  Check if the column contains string values and remove spaces and capitalize the first letter of each string
            df_filled[col] = df_filled[col].str.replace(' ', '').str.capitalize()

    return df_filled

# Apply the function to clean and standardize the DataFrames
members = detect_and_replace_missing_info(members)
membership = detect_and_replace_missing_info(membership)
payment = detect_and_replace_missing_info(payment)

########################################################################################################################

# Merge the 'payment' DataFrame with the 'members' DataFrame to include member data alongside payment history.
# Uses a left join on the 'Medlemsnummer' column to keep all rows from 'payment' and match with 'members' where possible.
historic_payment_with_member_data = pd.merge(payment, members, how='left',
                                             on=["Medlemsnummer"])

########################################################################################################################

def decide_member_age(df: pd.DataFrame, date_column: str, new_column_name: str):
    """
        Calculate the age of members based on their birth date and add it as a new column.

        Args:
            df (pd.DataFrame): The DataFrame containing member data.
            date_column (str): The column containing birth dates (format: '%d.%m.%Y').
            new_column_name (str): The name of the new column to store the calculated age.

        Returns:
            None: The function modifies the input DataFrame in place.
    """
    df[new_column_name] = pd.to_datetime(df[date_column], format="%d.%m.%Y", errors='coerce')
    # Calculate age in years: difference between today and the date in years
    df[new_column_name] = ((today - df[new_column_name]).dt.days // 365).fillna(-1).astype(int)

# Apply the function to calculate and add the 'Alder' (age) column to the DataFrame
decide_member_age(historic_payment_with_member_data, 'Fødselsdato', 'Alder')

########################################################################################################################
def decide_range(age_group: str):
    """
     Parse an age range string into minimum and maximum values.

    Args:
        age_group (str): A string representing an age range, e.g., "20-30" or "50+".

    Returns:
        tuple: A tuple containing the minimum and maximum age values as integers.
               For age groups with '+', max is set to infinity.

    Raises:
        ValueError: If the age group string does not match an expected format.
    """
    if '-' in age_group:
        # Split the string into start and end of the range and convert to integers
        start, end = map(int, age_group.split('-'))
    elif '+' in age_group:  # Case where the range has a '+', e.g., "50+"
        # Extract the numeric value before the '+' and set the range star
        start = list(map(int, re.findall(r'\d+', age_group)))[0] + 1
        end = np.inf  # Using NumPy's infinity for no upper limit
    else:
        raise ValueError(f"Unexpected format: {age_group}")
    return start, end

# Apply the `decide_range` function to the 'Aldersgruppe' column in the 'membership' DataFrame
# Extracts the min and max age values and creates two new columns: 'MinAlder' and 'MaxAlder'
membership[['MinAlder', 'MaxAlder']] = membership['Aldersgruppe'].apply(
    lambda x: pd.Series(decide_range(x))  # Convert the tuple into a Series for DataFrame assignment
)

########################################################################################################################
# Rename the column 'Medlemstype' to 'MedlemstypeGammel' in the DataFrame
historic_payment_with_member_data.rename(columns={'Medlemstype': 'MedlemstypeGammel'}, inplace=True)

########################################################################################################################

# Merge 'historic_payment_with_member_data' with the 'membership' DataFrame
# Use a query to filter rows where the member's age ('Alder') falls within the defined age range ('MinAlder', 'MaxAlder')
historic_payment_with_member_data = historic_payment_with_member_data.merge(membership, on="Periode",
                                                                            how="left").query(
    "Alder >= MinAlder and Alder <= MaxAlder")

# Rename the 'Medlemstype' column from the membership data to 'MedlemstypeNy'
historic_payment_with_member_data.rename(columns={'Medlemstype': 'MedlemstypeNy'}, inplace=True)

########################################################################################################################

# Create a new column 'FeilMedlemstype' to flag discrepancies between old and new membership types
# This compares 'MedlemstypeGammel' (old membership type) with 'MedlemstypeNy' (new membership type)
historic_payment_with_member_data['FeilMedlemstype'] = historic_payment_with_member_data['MedlemstypeGammel'] != \
                                                       historic_payment_with_member_data['MedlemstypeNy']

# Create a new column 'FeilBetaling' to flag discrepancies between actual payment and expected membership fee
# This compares 'Beløp' (actual payment) with 'Kontingent' (expected membership fee)
historic_payment_with_member_data['FeilBetaling'] = historic_payment_with_member_data['Beløp'] != \
                                                    historic_payment_with_member_data['Kontingent']

# Create a new column 'Tilbakebetaling' to calculate any refund owed
# This subtracts the actual payment ('Beløp') from the expected membership fee ('Kontingent')
historic_payment_with_member_data['Tilbakebetaling'] = historic_payment_with_member_data['Kontingent'] - \
                                                       historic_payment_with_member_data['Beløp']

########################################################################################################################

# Define the desired column order for the final DataFrame
new_order = ['Innbetalt_dato', 'Periode', 'Medlemsnummer', 'Fødselsdato', 'Alder', 'Aldersgruppe', 'Fornavn',
             'Etternavn', 'Kjønn', 'Gateadresse', 'Postnummer', 'Poststed', 'MedlemstypeGammel', 'MedlemstypeNy',
             'FeilMedlemstype', 'Kontingent', 'Beløp', 'FeilBetaling', 'Tilbakebetaling']

# Reorganize the columns in the 'historic_payment_with_member_data' DataFrame according to the 'new_order'
historic_payment_with_member_data = historic_payment_with_member_data[new_order]

# Save the finale DataFrame to an Excel file named 'results.xlsx'
historic_payment_with_member_data.to_excel('results.xlsx', index=False)

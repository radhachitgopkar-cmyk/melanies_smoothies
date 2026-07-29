# Import Python packages
import streamlit as st
import requests
from snowflake.snowpark.functions import col

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Create the title and description
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write("""
Choose the fruits you want in your custom Smoothie!
""")

# Ask for the name on the smoothie
name_on_order = st.text_input("Name on Smoothie:")

st.write("The name on your Smoothie will be:", name_on_order)

# Get the fruit options and API search values from Snowflake
my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(
    col("FRUIT_NAME"),
    col("SEARCH_ON")
)

# Convert the Snowpark DataFrame to a pandas DataFrame
pd_df = my_dataframe.to_pandas()

# Allow the user to choose up to five ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

# Create the ingredients string
ingredients_string = ""

# Display nutrition information for each selected fruit
if ingredients_list:

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + " "

        # Find the corresponding SEARCH_ON value
        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        # Display the selected fruit name
        st.subheader(fruit_chosen + " Nutrition Information")

        try:
            # Call the SmoothieFroot API using SEARCH_ON
            smoothiefroot_response = requests.get(
                f"https://my.smoothiefroot.com/api/fruit/{search_on}",
                timeout=10
            )

            # Raise an error for unsuccessful responses
            smoothiefroot_response.raise_for_status()

            # Display the API results
            st.dataframe(
                data=smoothiefroot_response.json(),
                use_container_width=True
            )

        except requests.exceptions.RequestException:
            st.error(
                "Nutrition information could not be found for "
                + fruit_chosen
                + "."
            )

# Submit button
if st.button("Submit Order"):

    if not name_on_order:
        st.warning("Please enter a name for the smoothie.")

    elif not ingredients_list:
        st.warning("Please choose at least one ingredient.")

    else:
        # Escape apostrophes before creating the SQL statement
        safe_ingredients = ingredients_string.replace("'", "''")
        safe_name = name_on_order.replace("'", "''")

        # Build the INSERT statement
        sql_insert = (
            "INSERT INTO SMOOTHIES.PUBLIC.ORDERS "
            "(INGREDIENTS, NAME_ON_ORDER) "
            "VALUES ('"
            + safe_ingredients
            + "','"
            + safe_name
            + "')"
        )

        try:
            # Run the INSERT statement
            result = session.sql(sql_insert)
            result.collect()

            # Confirmation message
            st.success(
                "✅ Your Smoothie is ordered, "
                + name_on_order
                + "!"
            )

        except Exception as error:
            st.error("Your smoothie order could not be submitted.")
            st.exception(error)

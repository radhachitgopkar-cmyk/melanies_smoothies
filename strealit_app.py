# Import Python packages
import streamlit as st
import requests
from snowflake.snowpark.functions import col

# Get the current credentials
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

# Get the fruit options from the Snowflake table
my_dataframe = session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS").select(col("FRUIT_NAME"),col("SEARCH_ON"))
st.dataframe(data=my_dataframe, use_container_width=True)
st.stop()

# Convert the Snowpark DataFrame to a pandas DataFrame
pd_df = my_dataframe.to_pandas()

# Allow the user to choose up to five ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

# Convert the selected fruits into one text string
ingredients_string = ""

for fruit_chosen in ingredients_list:
    ingredients_string += fruit_chosen + " "
    st.subheader(fruit_chosen + ' Nutrition Information')

    # Call the SmoothieFroot API for the selected fruit
    smoothiefroot_response = requests.get(
        "https://my.smoothiefroot.com/api/fruit/" + fruit_chosen
    )

    # Display the nutrition information
    sf_df = st.dataframe(
        data=smoothiefroot_response.json(),
        use_container_width=True
    )

# Submit button
if st.button("Submit Order"):

    # Escape apostrophes entered by the user
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

    # Run the INSERT statement
    result = session.sql(sql_insert)
    result.collect()

    # Confirmation message
    st.success(
        "✅ Your Smoothie is ordered, "
        + name_on_order
        + "!"
    )

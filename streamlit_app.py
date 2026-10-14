# Import python packages
import streamlit as st
import os
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
  """ Choose the fruits you want in your custom Smoothie! """
)

# Customer name input
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake and retrieve the fruit options
conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))
session = conn.session()

my_dataframe = session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS").select(col("FRUIT_NAME"),col("SEARCH_ON"))

# Convert Snowpark DataFrame to Pandas
pd_df = my_dataframe.to_pandas()

# Display the data in our Streamlit app
# st.dataframe(data=my_dataframe, use_container_width=True)

# Allow users to select multiple fruits
ingredients = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

# Display the selected ingredients
if ingredients:
    ingredients_string = ''

    # Loop through each selected fruit
    for fruit_chosen in ingredients:
        ingredients_string += fruit_chosen + ' '

        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        st.write(
            "The search value for ",
            fruit_chosen,
            " is ",
            search_on,
            "."
        )

        st.subheader(f"{fruit_chosen} Nutrition Information")

        fruit_name = fruit_chosen.lower().rstrip("s")

        fruit_response = requests.get(
            f"https://www.fruityvice.com/api/fruit/{fruit_name}",
            timeout=10
        )

        if fruit_response.status_code == 200:
            sf_df = st.dataframe(
                data=fruit_response.json(),
                use_container_width=True
            )
        else:
            st.warning(f"Nutrition information unavailable for {fruit_chosen}.")

    # Display selected ingredients
    st.write(ingredients_string)

    # Build the SQL INSERT statement
    my_insert_stmt = (
        "INSERT INTO SMOOTHIES.PUBLIC.ORDERS (INGREDIENTS, NAME_ON_ORDER) "
        "VALUES ('" + ingredients_string + "', '" + name_on_order + "')"
    )

    time_to_insert = st.button('Submit Order')

    # Insert the order into Snowflake
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")

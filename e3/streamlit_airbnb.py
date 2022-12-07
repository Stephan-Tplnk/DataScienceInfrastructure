from pymongo import MongoClient
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
form = st.form(key="form")
col1, col2, col3 = st.columns((1, 1, 1))
col4, col5 = st.columns((1, 2))

@st.cache(allow_output_mutation=True)
def load_data():
    client = MongoClient('mongodb+srv://student:nRfKfRqEtgWvznFD@cluster0.gu4ru.mongodb.net')
    db = client.get_database('sample_airbnb')
    all_data = pd.DataFrame(db.listingsAndReviews.find())
    all_data = pd.concat([all_data, pd.json_normalize(all_data["review_scores"])], axis = 1)
    all_data = pd.concat([all_data, pd.json_normalize(all_data["address"])], axis=1)
    all_data = pd.concat([all_data, pd.DataFrame(all_data["location.coordinates"].tolist(), index=all_data.index)], axis=1)
    all_data = pd.concat([all_data, pd.DataFrame(all_data["location.coordinates"].tolist(), index=all_data.index, columns = ["longitude", "latitude"])], axis=1)

    all_data["price"] = all_data["price"].astype(str).astype(float)
    all_data["longitude"] = all_data["longitude"].astype(str).astype(float)
    all_data["latitude"] = all_data["latitude"].astype(str).astype(float)
    all_data["bathrooms"] = all_data["bathrooms"].astype(str).astype(float)
    all_data["cleaning_fee"] = all_data["cleaning_fee"].astype(str).astype(float)

    return all_data

def filter_by_country(data):
    select = col1.multiselect('Country:', [''] + list(data['country'].unique()))
    if select:
        return data[data['country'].isin(select)]
    return data

def filter_by_price(data):
    minimum = min(data['price'])
    maximum = max(data['price'])
    lower = col1.number_input("Lowest Price:", min_value=minimum, max_value=maximum, value=minimum)
    highest = col1.number_input("Highest Price:", min_value=minimum, max_value=maximum, value=maximum)
    return data[data['price'].between(*(lower, highest))]

def filter_by_room_type(data):
    roomtypes = sorted(list(data["room_type"].drop_duplicates()))
    select = col1.multiselect("Room Type:", roomtypes)
    if select:
        return data[(data['room_type'].isin(roomtypes))]
    return data

def filter_by_property(data):
    properties = sorted(list(data["property_type"].drop_duplicates()))
    select = col1.multiselect("Property:", properties)
    if select:
        return data[(data['property_type'].isin(select))]
    return data

def filter_by_amenities(data):
    amenities = set(sum(data["amenities"], []))
    _ = [amenities.discard(x) for x in ['', 'translation missing: en.hosting_amenity_49', 'translation missing: en.hosting_amenity_50']]
    amenities = sorted(amenities)
    select = col1.multiselect("Amenities:", amenities)
    if select:
        return data[data["amenities"].astype(str).apply(eval).apply(lambda x: all(elem in x for elem in select))]
    return data

def filter_by_reviewscores(data):
    loc = col4.slider("Location", 0, 10, (0, 10))
    check = col4.slider("Check In", 0, 10, (0, 10))
    clean = col4.slider("Cleanliness", 0, 10, (0, 10))
    val = col4.slider("Value", 0, 10, (0, 10))
    rat = col4.slider("Overall Rating", 0, 100, (0, 100))

    drop = col4.checkbox('Exlcude No Reviews', value=False)

    if drop:
        return data[(data['review_scores_location'].between(*loc)) &
                    (data['review_scores_checkin'].between(*check)) &
                    (data['review_scores_cleanliness'].between(*clean)) &
                    (data['review_scores_value'].between(*val)) &
                    (data['review_scores_rating'].between(*rat))]

    return data[(data['review_scores_location'].between(*loc) | data['review_scores_location'].isna()) &
                (data['review_scores_checkin'].between(*check) | data['review_scores_checkin'].isna()) &
                (data['review_scores_cleanliness'].between(*clean) | data['review_scores_cleanliness'].isna()) &
                (data['review_scores_value'].between(*val) | data['review_scores_value'].isna()) &
                (data['review_scores_rating'].between(*rat) | data['review_scores_rating'].isna())]

def render_visualisations(data):
    col2.map(data[["longitude", "latitude"]])

    fig = plt.figure(figsize=(7, 5))
    plt.hist(data[['review_scores_location', 'review_scores_checkin', 'review_scores_cleanliness', 'review_scores_value']])
    plt.legend(labels=['Location', 'Checkin', 'Cleanliness', 'Value'], loc='upper left')
    col3.pyplot(fig)

    col5.table(data.describe()[['price', 'cleaning_fee', 'accommodates', 'bedrooms', 'beds', 'bathrooms', 'number_of_reviews']].T)

    fig = plt.figure(figsize=(7, 1))
    plt.hist(data['price'], bins=100)
    col5.pyplot(fig)

def run():
    data = load_data()
    data = filter_by_country(data)
    data = filter_by_price(data)
    data = filter_by_room_type(data)
    data = filter_by_property(data)
    data = filter_by_amenities(data)
    data = filter_by_reviewscores(data)
    render_visualisations(data)

if __name__ == "__main__":
    run()
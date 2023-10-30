import bson
def add_element(dict, key, value):
    if key not in dict:
        dict[key] = []
    dict[key].append(value)

with open(r'dump_data/yelp_data.bson','rb') as f:
    data = bson.decode_all(f.read())

total_reviews = len(data)
data_reviews_only = {}
for i in range(total_reviews):
    # print(i)
    # Check that name and review key exist
    if "name" in data[i] and "reviews" in data[i]:
        name = data[i]["name"] # restuarant name
        reviews = data[i]["reviews"] # all reviews
        add_element(data_reviews_only, name, reviews)
print(total_reviews)
print(len(data_reviews_only))
import bson
def add_element(nested_dict, id_and_name, review):
    if id_and_name in nested_dict:
        # If the key exists, append the review to the existing list of reviews
        nested_dict[id_and_name].append(review)
    else:
        # If the key doesn't exist, create a new key-value pair
        nested_dict[id_and_name] = [review]


with open(r'dump_data/yelp_data.bson','rb') as f:
    data = bson.decode_all(f.read())

total_reviews = len(data)
data_reviews_only = {}
for i in range(total_reviews):
    # print(i)
    # Check that id, name, and review exist
    if ("name" in data[i]) and ("reviews" in data[i]) and ("id" in data[i]):
        id = data[i]["id"]
        name = data[i]["name"] # restuarant name
        reviews = data[i]["reviews"] # all reviews
        name_id = (id,name)
        add_element(data_reviews_only, name_id, reviews)
print(reviews)
print(total_reviews)
print(len(data_reviews_only))

get_id_and_name = list(data_reviews_only)

# get first reviews
for j in range(len(data_reviews_only)):
    id = get_id_and_name[j][0]
    name = get_id_and_name[j][1]
    all_reviews = data_reviews_only[(id,name)][0]

print(all_reviews)

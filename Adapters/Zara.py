import json

dataSource = "../Data/Zara/output.json"
cleanDataSource = "../Data/Zara/clean_output.json"
zaraProducts = json.load(open(dataSource))

def itemInList(list, item):
    # Checks if the item is in the list
    for i in range(len(list)):
        if list[i] == item:
            return True
    return False

def getCategories():
    # Returns all the distint categories of Zara
    categories = []
    for product in zaraProducts:
        category = product["category"]
        if(not itemInList(categories, category)):
            categories.append(category)

    return categories

def getSubCategories():
    # Returns all the distint sub-categories of Zara
    subCategories = []
    for product in zaraProducts:
        for cat in product["sub_category"].split(" | "):
            if(not itemInList(subCategories, cat)):
                subCategories.append(cat)

    return subCategories

def getProductSubCategories(subCategories):
    # Returns a list of sub-categories a product belongs to
    lstSubCategories = []
    for category in subCategories.split(" | "):
        if(category != ""):
            lstSubCategories.append(category)

    return lstSubCategories

def getProductColors(colors):
    # Return the color of the product
    color = colors.split(" | ")
    color = color[0].split("Colour ")
    try:
        color = color[1]
    except:
        color = ""

    return color

def getProductImages(images):
    # Returns a list of product images
    lstImages = []
    for img in images:
        lstImages.append(img)

    return lstImages    

def cleanData():
    products = []
    jsonFile = open(cleanDataSource, "w")

    num = 0     # number of products parsed
    for product in zaraProducts:
        num += 1
        name = product["name"]
        description = product["description"]
        category = product["category"]
        subCategories = getProductSubCategories(product["sub_category"])
        color = getProductColors(product["color"])
        images = getProductImages(product["images"])
        price = product["price"]
        sku = product["sku"]
        url = product["url"]

        dictionary = {
            "name": name, 
            "description": description, 
            "category": category, 
            "subCategories": subCategories,
            "color": color,
            "images": images,
            "price": price,
            "sku": sku,
            "url": url
        }
        products.append(dictionary)

    jsonString = json.dumps(products)
    jsonFile.write(jsonString)
    jsonFile.close()
    print("Total products cleaned up: " + str(num))


cleanData()
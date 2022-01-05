import json
from Functions import *

dataSource = "../Data/Zara/output.json"
cleanDataSource = "../Data/Zara/clean_output.json"

zaraProducts = json.load(open(dataSource))

def displayData():
    num = 0
    for product in zaraProducts:
        num += 1
        print("ID: " + str(num))    
        print("Name: " + product["name"])
        print("Description: " + product["description"])
        print("Category: " + product["category"])
        
        sub_category = ""
        for cat in product["sub_category"].split(" | "):
            if (sub_category != ""):
                sub_category = sub_category + ", " + cat
            else:
                sub_category = cat
        print("Sub-Category: " + sub_category)

        color = product["color"].split(" | ")
        color = color[0].split("Colour ")
        try:
            color = color[1]
        except:
            color = ""
        print("Color: " + color)

        images = []
        for img in product["images"]:
            images.append(img)

        print(images)
        
        print("Price: " + product["price"])
        print("SKU: " + product["sku"])
        print("URL: " + product["url"])
        print("")

def getCategories():
    categories = []
    for product in zaraProducts:
        category = product["category"]
        if(not itemInList(categories, category)):
            categories.append(category)

    return categories

def getSubCategories():
    subCategories = []
    for product in zaraProducts:
        for cat in product["sub_category"].split(" | "):
            if(not itemInList(subCategories, cat)):
                subCategories.append(cat)

    return subCategories

def getProductSubCategories(subCategories):
    lstSubCategories = []
    for category in subCategories.split(" | "):
        if(category != ""):
            lstSubCategories.append(category)

    return lstSubCategories

def getProductColors(colors):
    color = colors.split(" | ")
    color = color[0].split("Colour ")
    try:
        color = color[1]
    except:
        color = ""

    return color

def getProductImages(images):
    lstImages = []
    for img in images:
        lstImages.append(img)

    return lstImages    

def cleanData():
    products = []
    jsonFile = open(cleanDataSource, "w")

    num = 0
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
    print("Total products: " + str(num))


cleanData()
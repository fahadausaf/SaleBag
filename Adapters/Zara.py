import json
from Functions import *
#import Functions

dataSource = "../Data/Zara/output.json"

f = open(dataSource)
data = json.load(f)

def displayData():
    num = 0
    for product in data:
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
        
        print("Price: " + product["price"])
        print("SKU: " + product["sku"])
        print("URL: " + product["url"])
        print("")

def getCategories():
    categories = []
    for product in data:
        category = product["category"]
        if(not itemInList(categories, category)):
            categories.append(category)

    print(categories)

def getSubCategories():
    subCategories = []
    for product in data:
        for cat in product["sub_category"].split(" | "):
            if(not itemInList(subCategories, cat)):
                subCategories.append(cat)

    print(subCategories)

getSubCategories()
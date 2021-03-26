#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from bs4 import BeautifulSoup, NavigableString
import requests
import re
import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="senegal"
)

# In[ ]:


class EthnieData:
    def __init__(self):
        url = "https://www.axl.cefan.ulaval.ca/afrique/senegal.htm"
        html_doc = requests.get(url).text
        self.soup = BeautifulSoup(html_doc, 'html.parser')
        self.data_type = "ETHNIE"
        self.description_template = "L'ethnie {} compte une population d'environ {}, ce qui correspond à {} de la population nationale. Leur langue maternelle est le {}."

    def get_data(self):
        list_data = []
        table = self.soup.find(id="table4")
        table_lines = table.find_all("tr")
        del table_lines[0]
        del table_lines[-1]
        del table_lines[-1]
        
        for line in table_lines:
            data = self.get_info(line)
            list_data.append(data)
        return list_data
    
    def get_info(self, line):
        td_list = [re.sub('\s+', ' ', x.text) for x in line.contents if not isinstance(x, NavigableString)]
        del td_list[-1]
        
        nom = td_list[0]
        population = td_list[1]
        pourcentage = td_list[2]
        langue = td_list[3]
        
        url_photo = ""
        description = self.description_template.format(nom, population, pourcentage, langue)
        
        return {
            "type": self.data_type,
            "url_photo": url_photo,
            "nom": nom,
            "description": description
        }


# In[ ]:


class AuteurData:
    def __init__(self):
        url = "https://www.google.com/search?sxsrf=ALeKk02nfA2caaCOZcqelWe4rSUWfWQqeg%3A1604739700443&ei=dGKmX9G6GsGx8gKl1JyADQ&q=s%C3%A9n%C3%A9gal+auteur"
        html_doc = requests.get(url).text
        self.soup = BeautifulSoup(html_doc, 'html.parser')
        self.data_type = "AUTEUR"
    
    def get_data(self):
        list_data = []
        list_cards = self.soup.find_all("a", class_="ct5Ked")
        for card in list_cards:
            data = self.get_info(card)
            list_data.append(data)
        return list_data
        
    def get_description(self, url):
        url = "https://www.google.com" + url
        html_doc = requests.get(url).text
        soup = BeautifulSoup(html_doc, 'html.parser')
        description = soup.find("div", attrs={"data-attrid": "description"}).text.stip()
        return description
    
    def get_info(self, card):
        url_photo = card.find("img").get('src')
        names = card.find_all("div", class_="FozYP")
        nom = "".join(names)
        try:
            description = self.get_description(card.get("href"))
        except:
            description = ""
        
        return {
            "type": self.data_type,
            "url_photo": url_photo,
            "nom": nom,
            "description": description
        }


# In[ ]:


class ChanteurData:
    def __init__(self):
        url = "https://www.google.com/search?rlz=1C1SQJL_frBJ879BJ879&sxsrf=ALeKk00i0HItSu54RiB_Ym8kexaqiEJlYg%3A1604740896903&ei=IGemX9nMNoqhgQaJqIPoAQ&q=s%C3%A9n%C3%A9gal+chanteur&oq=s%C3%A9n%C3%A9gal+chanteur&gs_lcp=CgZwc3ktYWIQAzIGCAAQFhAeMggIABAWEAoQHjIGCAAQFhAeMgYIABAWEB46BAgAEEdQlLkGWJS5BmDcwAZoAHADeACAAdkBiAHZAZIBAzItMZgBAKABAqABAaoBB2d3cy13aXrIAQjAAQE&sclient=psy-ab&ved=0ahUKEwjZ3PbYjfDsAhWKUMAKHQnUAB0Q4dUDCA0&uact=5"
        html_doc = requests.get(url).text
        self.soup = BeautifulSoup(html_doc, 'html.parser')
        self.data_type = "CHANTEUR"
    
    def get_data(self):
        
        list_data = []
        list_cards = self.soup.find_all("a", class_="BVG0Nb")
        for card in list_cards:
            data = self.get_info(card)
            list_data.append(data)
        return list_data
        
    def get_description(self, url):
        url = "https://www.google.com" + url
        html_doc = requests.get(url).text
        soup = BeautifulSoup(html_doc, 'html.parser')
        description = soup.find("div", attrs={"data-attrid": "description"}).text.stip()
        return description
    
    def get_info(self, card):
        url_photo = card.find("img").get('src')
        names = card.find_all("div", class_="FozYP")
        nom = "".join(names)
        try:
            description = self.get_description(card.get("href"))
        except:
            description = ""
            
        return {
            "type": self.data_type,
            "url_photo": url_photo,
            "nom": nom,
            "description": description
        }


# In[ ]:


chanteurs = ChanteurData().get_data()
chanteurs


# In[ ]:


# obj_auteur_data = AuteurData()
# obj_chanteur_data = ChanteurData()
# obj_ethnie_data = EthnieData()

# auteurs = obj_auteur_data.get_data()
# chanteurs = obj_chanteur_data.get_data()
# ethnies = obj_ethnie_data.get_data()

auteurs = AuteurData().get_data()
chanteurs = ChanteurData().get_data()
ethnies = EthnieData().get_data()


# In[ ]:


culture_data = []
culture_data.extend(auteurs)
#print(culture_data)
#culture_data.extend(chanteurs)
#print(culture_data)
#culture_data.extend(ethnies)
#print(culture_data)


# In[ ]:


#print(culture_data)
 
val1=[
('CHANTEUR','data:image/gif;base64,R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==','youssou',''), 
('CHANTEUR','data:image/gif;base64,R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==','Ismaila',''),
]

"""
val2=[
('ETHNIE','',' Wolofs et Lebous',"L'ethnie  Wolofs et Lebous compte une population d'environ 5 208 000, ce qui correspond à  39,7 % de la population nationale. Leur langue maternelle est le  wolof."),
('ETHNIE','',"Peuls, Poulars, Fula, Toucouleurs,","L'ethnie  Peuls, Poulars, Fula, Toucouleurs,  compte une population d'environ 3 452 000, ce qui correspond à  26,3 % de la population nationale. Leur langue maternelle est le  peul.")
]
"""

mycursor = mydb.cursor()
sql = "INSERT INTO cultures (type,url_photo,nom,description) VALUES (%s,%s,%s,%s)"
mycursor.executemany(sql,val1)
mydb.commit()

print(mycursor)

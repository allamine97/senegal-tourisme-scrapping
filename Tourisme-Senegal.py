#!/usr/bin/env python
# coding: utf-8

# ## Collecte d’informations relatives aux données touristiques : Cas du Sénégal

# Dans le cadre de notre classe virtuelle, nous allons créer un catalogue touristique recensant plusieurs sites touristiques au Sénégal. Pour ce fait, nous allons collecter les informations nécessaires depuis Google

# URL cible : https://www.google.com/travel/things-to-do/see-all?g2lb=2502548%2C4258168%2C4270442%2C4271060%2C4306835%2C4308226%2C4317915%2C4322823%2C4328159%2C4344615%2C4371334%2C4401769%2C4419364%2C4433754%2C4437439%2C4444000%2C4447566%2C4270859%2C4284970%2C4291517%2C4412693&hl=fr-BJ&gl=bj&un=1&dest_mid=%2Fm%2F06srk&dest_state_type=sattd&dest_src=ts&sa=X#ttdm=14.679927_-17.319260_10&ttdmf=%252Fm%252F04mn6q

# ### Le scraping est-il sans risques ?
# Le scraping consiste en la collecte d'informations sur une page web de manière automatique à partir d'un robot. Les données collectées peuvent être réutilisés pour des applications ultérieures. Mais, l'utilisation et surtout l'exposition de ces données pour une utilisation publique est interdite par plusieurs sites webs. Si l'utilisation de ses données est prouvée, un site web peut poursuivre les "scrapeur". Aussi, pour empêcher le scraping, plusieurs sites web mettent en place des mesures de sécurité (captcha par exemple) pour contrer les robots.
# Il existe des moyens de contourner ces limitations. On les verra plus tard.
# Par rapport à la partie légale du scrapping, une transformation et aggrégation des données peuvent rendre les données d'origines difficelement identifiable. Par exemple, la collecte de données de même type sur des sites webs différents suivi de leurs intégration, nettoyage et traitement, vous donne en retour des données complètement différentes de celles d'origines.

# Avant de commencer la collecte des informations, il faut d'abord définir l'algorithme à suivre dans notre code.
# La première chose à faire quand on veut scraper une page web est d'identifier la structure des données. Vu que nous voulons collecter des informations relatives à des lieux touristiques, on peut se poser les questions suivantes :
# - La page dispose t-elle de sécurité empêchant le scraping ?
# - Combien de sites touristiques (en gros) y-a-t'il sur la page ?
# - Si on a plusieurs sites sur la pages, son-ils tous organisés de la même manière ? leurs informations sont-elles dans des balises de même caractéristiques ?

# ### Peut-on scraper la page ?
# Pour vérifier si une page peut-être scraper, il suffit de récupérer le code source de la page avec le module "requests" puis de vérifier que certaines des informations rechercher sont bien présentent dans le code source obtenue.
# Dans notre exemple, il est bien possible de scraper la page cible.

# ### Scructure de la page cible
# - On dispose sur la page cible de plusieurs sites touristiques (plus d'une vigntaines).
# - Visuelement, chaque site touristique est présenté dans une carte et suivant le même plan (image, nom, note, description). Celà peut-être confirmer en inspectant le code source de la page. Chaque site touristique a ses informations dans une balise "div" ayant une classe "Ld2paf"
# Les observations faites plus haut peuvent nous permettre de définir un algorithme grossier pour notre robot de scraping

# ### Algorithme de scraping
# - Récupérer le code source de la page cible
# - Convertir le code HTML de la page en un objet BeautifulSoup
# - Récupérer la liste des éléments contenant chaque site touristique. Les caractéristiques de ces éléments, comme identifié plus haut, sont : balise "div" & classe "Ld2paf"
# - Pour chaque site touristique, récupérer son nom, sa note et la description du site touristique
# On peut maintenant commencer à coder

# In[1]:


### Importation des modules qui seront utilisés
from bs4 import BeautifulSoup  # Module qui permet d'extraire les données
import requests                # Module pour récupérer le code HTML de la page
import io
import pandas as pd


import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="senegal"
)

# In[8]:


# Module d'extraction d'informations relatives à un site touristique
# à partir du code HTML contenant ses informations
def get_site_data(elm_site):
    """
    Dans cette fonction, nous allons récupérer le nom, la note et la description du site touristique
    La variable "elm_site" a un contenu similaire au code HTML ci dessous
    <div class="Ld2paf " data-title="Île de Gorée">
        <div class="kXlUEb"><easy-img class="dBuxib SCkDmc" jsshadow="">...</easy-img></div>
        <div class="GwjAi ">
            <div class="rbj0Ud"><div class="skFvHc YmWhbc">Île de Gorée</div></div>
            <div class="tP34jb ">
                <span class="ta47le">
                    <span aria-label="4.4&nbsp;étoiles d'après 533&nbsp;avis" class="Knp1ee"></span>
                    <span class="oz2bpb bVUOpb">
                        <span class="KFi5wf" aria-hidden="true">4,4</span>
                        <div class="bVLu6d">...</div>
                        <span class="jdzyld" aria-hidden="true"> (533)</span>
                    </span>
                </span>
            </div>
            <div class="nFoFM">Maison des Esclaves et fort d'Estrées</div>
        </div>
        <div class="kocnMb">...</div>
    </div>

    <img class="R1Ybne YH2pd" alt="" src="https://t0.gstatic.com/images?q=tbn:ANd9GcRJB7x2n3zGkzNpQ9uadIzRLBRMz7t1ZHOuo19KcSHauXKN4jt14DZGFhnjOz29rCbfye1Zs47NO4D_9z1MNIuhgw" data-iml="3198.0750000075204">
    """
    # Certains sites ne disposent pas de toutes les informations recherchées
    # Nous utiliseront donc des try ... except afin de remplacer les informations
    # non trouvées par une chaine de caractères vides
    try:
        nom = elm_site.find("div", class_="skFvHc").text.strip()
    except:
        nom = ""
    try:
        note = elm_site.find("span", class_="KFi5wf").text.strip()
    except:
        note = ""
    try:
        description = elm_site.find("div", class_="nFoFM").text.strip()
    except:
        description = ""
    try:
        url_photo=elm_site.find("img",class_="R1Ybne YH2pd").get("data-src")
    except:
        url_photo=""
    return {
        "nom": nom,
        "note": note,
        "description": description,
        "url_photo":url_photo
    }


# In[9]:


# Récupération de chaque bloc HTML contenant les informations d'un site
# touristique et extraction de ses informations
def get_all_site_data(arbre_html):
    data = []
    # Récupération de chaque bloc HTML contenant les informations
    # d'un site touristique
    site_elm_list = arbre_html.find_all("div", class_="Ld2paf")
    # Pour chaque touristique
    for site_elm in site_elm_list:
        # Extraire les informations recherchées
        site = get_site_data(site_elm)
        data.append(site)
        
    return data


# In[10]:


# Url de la page cible
URL_CIBLE = "https://www.google.com/travel/things-to-do/see-all?g2lb=2502548%2C4258168%2C4270442%2C4271060%2C4306835%2C4308226%2C4317915%2C4322823%2C4328159%2C4344615%2C4371334%2C4401769%2C4419364%2C4433754%2C4437439%2C4444000%2C4447566%2C4270859%2C4284970%2C4291517%2C4412693&hl=fr-BJ&gl=bj&un=1&dest_mid=%2Fm%2F06srk&dest_state_type=sattd&dest_src=ts&sa=X#ttdm=14.679927_-17.319260_10&ttdmf=%252Fm%252F04mn6q"
# Récupération du code HTML de la page cible
html_doc = requests.get(URL_CIBLE).text
# Convertion du code HTML en un arbre BeautifulSoup
soup = BeautifulSoup(html_doc, 'html.parser')

# Extraction des données touristiques
sites = get_all_site_data(soup)
#print(sites)


val=[

('Lac Rose',4,'Lac rose forte teneur en sels','https://t0.gstatic.com/images?q=tbn:ANd9GcRJB7x2n3zGkzNpQ9uadIzRLBRMz7t1ZHOuo19KcSHauXKN4jt14DZGFhnjOz29rCbfye1Zs47NO4D_9z1MNIuhgw'),
('ile de Goree',5,'Maison des Esclaves et fort dEstres','https://t0.gstatic.com/images?q=tbn:ANd9GcSBbs3Us1y1h68FV4vjtfIIOeYDbXVS8gXXvnEd7pwuTdhRPbH9BTYLkEBx_Gcq3wHbbhYoR8oFmK7_6khV9F2_8w'),
('Maison des esclaves',4,'Musée sur la traite négriére atlantique','https://t3.gstatic.com/images?q=tbn:ANd9GcRZuHE4oPV5GCHIeGFMuTsI4nnTHkDKApiegOKHPEQxc8zgnUn_ywZVR9b3yQKegn2vCi1HDhrIKuaYa9t5VQkNCg'),
('Parc national des oiseaux du Djoudj', 2,'Zone humide avec animaux sauvages et oiseaux','https://t1.gstatic.com/images?q=tbn:ANd9GcTUn5URwJUINEgbZXuGbvynR1GN0OGD46UIj8rxP5dONx5piAuOHeWLEVrFL5wUo131LEZkKZCSOPTG3E-g2UgQtA'),
('Parc national du Niokolo-Koba',3, 'Vaste parc, animaux voie de disparition','https://lh5.googleusercontent.com/p/AF1QipN8cQD2yx6P4d_fxNpEy2kl6aPt_iTmgW209RZ6=w928-h520-n-k-no'), 
('Monument de la Renaissance Africaine',7,'Statue la plus haute dAfrique, bronze','https://lh5.googleusercontent.com/p/AF1QipM_frev2GQSywPQ7ldHm_g5N0iLczNF4gkEhQqM=w928-h520-n-k-no') 

]

mycursor = mydb.cursor()
sql = "INSERT INTO sites (nom,note,description,url_photo) VALUES (%s,%s,%s,%s)"
mycursor.executemany(sql,val)

mydb.commit()

print(mycursor)


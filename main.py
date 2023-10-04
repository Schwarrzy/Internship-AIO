import requests
from bs4 import BeautifulSoup
import discord
from datetime import datetime
import os
import sys
import json

base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
json_file = os.path.join(base_dir, 'Setup.json')

with open(json_file) as f:
    data = json.load(f)

url = data['URL']
channel_serveur = int(data['channel_id'])
token_discord = data['token']

# Envoi de la requête GET
response = requests.get(url)

# Vérification du code de statut HTTP
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    print("Reponse 200 done")

    # Sélection des éléments <a> contenant les titres des offres d'emploi
    job_links = soup.find_all('a', class_='font-subtitle-3-medium job-title job-title-spacing')

    # Sélection des éléments <div> contenant le nom de l'entreprise
    company_divs = soup.find_all('div', class_='font-body-3 company col ng-star-inserted')

    # Sélection des éléments <span> contenant les détails de l'offre (lieu ou date)
    details_spans = soup.find_all('span', class_='dot-divider')

    # Sélection des éléments <img> contenant les images de l'annonce
    image_tags = soup.find_all('img', itemprop='image')

    # Ensemble pour stocker les titres des offres précédentes
    offres_precedentes = set()

    # Liste pour stocker les nouvelles offres
    nouvelles_offres = []

    title = None
    company = None
    location = None
    date = None
    image_url = None
    job_url = None

    # Charger les titres des offres précédentes depuis un fichier (s'il existe)
    try:
        with open('offres_precedentes.txt', 'r', encoding='utf-8') as fichier:
            for line in fichier:
                title = line.strip()
                offres_precedentes.add(title)
    except FileNotFoundError:
        pass

    # Fonction pour envoyer un message sur Discord
    async def send_discord_message(embed):
        await client.wait_until_ready()  # Attendre que le client soit prêt
        channel_id = channel_serveur  # ID du canal où vous voulez envoyer le message
        channel = client.get_channel(channel_id)
        
        # Obtenir la date et l'heure actuelles
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%d %b %Y - %H:%M")
        
        # Ajoutez la date et l'heure en bas de l'embed
        embed.set_footer(text=formatted_datetime)

        print("Message envoyé")
        if channel is not None:
            await channel.send(embed=embed)
        else:
            print(f"Le canal avec l'ID {channel_id} n'a pas été trouvé.")

    # Informations d'identification pour se connecter à Discord
    token = token_discord

    # Créer les intentions pour le client Discord
    intents = discord.Intents.default()

    # Créer le client Discord
    client = discord.Client(intents=intents)

    # Boucle à travers les détails de chaque offre
    for i, (job_link, company_div, details_span, image_tag) in enumerate(zip(job_links, company_divs, details_spans, image_tags)):
        title = job_link['title']
        company = company_div.text.strip()
        content = details_span.text.strip()
        
        # Obtenir l'URL de l'offre depuis la balise <a>
        job_url = job_link['href']

        # Vérifiez si le titre de l'offre existe déjà dans les offres précédentes
        if title not in offres_precedentes:
            # Vérifiez si le contenu se termine par "ago", ce qui indique la date de publication
            if content.endswith('ago'):
                date = content
            else:
                # Si ce n'est pas une date, considérez-le comme le lieu
                location = content

            # Récupérez l'URL de l'image
            image_url = image_tag['src']

            # Créez un embed pour chaque offre avec le titre intégrant le lien
            embed = discord.Embed(description=f"Entreprise : {company}\nLieu : {location if location else 'Inconnu'}\nDate de publication : {date if date else 'Inconnue'}")
            embed.set_author(name=title, url=job_url)  # Définit le titre cliquable avec l'URL
            embed.set_thumbnail(url=image_url)  # Définit l'image en haut à gauche du titre

            # Définissez la couleur de la bordure de l'embed
            embed.color = 0x00AE86

            # Ajoutez l'offre à la liste des nouvelles offres
            nouvelles_offres.append(embed)

            # Ajoutez le titre à l'ensemble des offres précédentes
            offres_precedentes.add(title)

    # Sauvegarder les titres des offres précédentes dans un fichier
    with open('offres_precedentes.txt', 'w', encoding='utf-8') as fichier:
        for title in offres_precedentes:
            fichier.write(f"{title}\n")

    # Méthode appelée lorsque le client Discord est prêt
    @client.event
    async def on_ready():
        print('Le client Discord est connecté.')
        if nouvelles_offres:
            for embed in nouvelles_offres:
                await send_discord_message(embed)  # Appeler la fonction pour envoyer un message

    # Méthode appelée lorsqu'une erreur se produit dans le client Discord
    @client.event
    async def on_error(event, *args, **kwargs):
        print('Erreur dans le client Discord :', event)
        raise

    # Démarrer le bot
    client.run(token)
    
else:
    print(f"La requête a échoué avec le code de statut {response.status_code}")

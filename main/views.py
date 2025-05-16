from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Medecin, Patient, RendezVous, Laboratoire, Pharmacien, Ordonnance, Disponibilite, ChatMessage
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
import http.client
import json
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.db import models
import os
from dotenv import load_dotenv
from pathlib import Path
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
import time
import openai

# Get the absolute path to IA.env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / 'allodocmedecins' / 'IA.env'

# Load environment variables from IA.env
load_dotenv(ENV_PATH)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authentification simple
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Rediriger vers le tableau de bord approprié
            if hasattr(user, 'patient'):
                return redirect('patient_dashboard')
            elif hasattr(user, 'medecin'):
                return redirect('medecin_dashboard')
            elif hasattr(user, 'laboratoire'):
                return redirect('laboratoire_dashboard')
            elif hasattr(user, 'pharmacien'):
                return redirect('pharmacien_dashboard')
            else:
                messages.error(request, "Type d'utilisateur non reconnu.")
                return redirect('home')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            return redirect('login')
    
    return render(request, 'registration/login.html')

# Create your views here.

def call_rapidapi_chat(messages):
    """
    Fonction pour interagir avec l'API ChatGPT via RapidAPI.
    Analyse les symptômes et fournit des conseils médicaux.
    """
    try:
        # Configuration de l'API RapidAPI
        conn = http.client.HTTPSConnection("chatgpt-42.p.rapidapi.com")
        
        # Préparation du prompt pour ChatGPT
        system_prompt = """Tu es un assistant médical virtuel. 
        Ta tâche est d'analyser les symptômes décrits par le patient et de fournir :
        1. Une analyse préliminaire des symptômes
        2. Des conseils généraux
        3. Des recommandations sur la nécessité de consulter un médecin
        IMPORTANT : Précise bien que tu n'es pas un médecin et que tes conseils ne remplacent pas une consultation médicale."""
        
        # Construction du message
        if isinstance(messages, list) and len(messages) > 0:
            user_message = messages[-1].get("content", "")
        else:
            user_message = str(messages)
            
        prompt = f"{system_prompt}\n\nPatient : {user_message}"
        
        payload = json.dumps({
            "text": prompt
        })
        
        headers = {
            'x-rapidapi-key': settings.OPENAI_API_KEY,
            'x-rapidapi-host': 'chatgpt-42.p.rapidapi.com',
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/aitohuman", payload, headers)
        res = conn.getresponse()
        data = res.read()
        result = json.loads(data.decode("utf-8"))
        
        # Adaptation pour différents formats de réponse
        if "result" in result:
            if isinstance(result["result"], str):
                return result["result"].strip()
            elif isinstance(result["result"], list) and result["result"]:
                return result["result"][0].strip()
        
        return f"Erreur API : {result}"
        
    except Exception as e:
        return f"Désolé, je ne peux pas traiter votre demande pour le moment. Erreur : {str(e)}"

def call_rapidapi_aitohuman(prompt):
    conn = http.client.HTTPSConnection("chatgpt-42.p.rapidapi.com")
    payload = json.dumps({
        "text": prompt
    })
    headers = {
        'x-rapidapi-key': os.getenv('RAPIDAPI_KEY', ''),
        'x-rapidapi-host': 'chatgpt-42.p.rapidapi.com',
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/aitohuman", payload, headers)
    res = conn.getresponse()
    data = res.read()
    result = json.loads(data.decode("utf-8"))
    # Adaptation pour différents formats de réponse
    if "result" in result:
        if isinstance(result["result"], str):
            return result["result"].strip()
        elif isinstance(result["result"], list) and result["result"]:
            return result["result"][0].strip()
    return f"Erreur API : {result}"

def get_user_location(request):
    """Récupère la localisation de l'utilisateur depuis la session ou utilise les coordonnées par défaut"""
    if 'user_location' in request.session:
        return request.session['user_location']
    
    # Coordonnées par défaut (Paris)
    default_location = {'lat': 48.8566, 'lng': 2.3522}
    request.session['user_location'] = default_location
    return default_location

def home(request):
    if not request.user.is_authenticated:
        return redirect('visitor_page')
        
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    chat_history = request.session['chat_history']
    
    # Récupérer la localisation de l'utilisateur
    user_lat = request.session.get('user_lat', 48.8566)  # Paris par défaut
    user_lng = request.session.get('user_lng', 2.3522)
    
    # Initialiser les listes de recommandations avec des coordonnées par défaut
    medecins_proches = Medecin.objects.all()
    for medecin in medecins_proches:
        if medecin.latitude is None:
            medecin.latitude = 48.8566
        if medecin.longitude is None:
            medecin.longitude = 2.3522
    
    laboratoires_proches = Laboratoire.objects.all()
    pharmacies_proches = Pharmacien.objects.all()
    
    if request.method == 'POST':
        if 'reset_chat' in request.POST:
            request.session['chat_history'] = []
            chat_history = []
        elif 'location' in request.POST:
            # Mettre à jour la localisation de l'utilisateur
            try:
                lat, lng = map(float, request.POST['location'].split(','))
                request.session['user_lat'] = lat
                request.session['user_lng'] = lng
                return JsonResponse({'status': 'success'})
            except:
                return JsonResponse({'status': 'error'})
        else:
            user_message = request.POST.get('message')
            if user_message:
                chat_history.append({"role": "user", "content": user_message})
                try:
                    ai_message = call_rapidapi_chat(chat_history)
                    chat_history.append({"role": "assistant", "content": ai_message})
                except Exception as e:
                    ai_message = f"Erreur lors de l'analyse : {e}"
                    chat_history.append({"role": "assistant", "content": ai_message})
                request.session['chat_history'] = chat_history
    
    return render(request, 'home.html', {
        'chat_history': chat_history,
        'medecins_proches': medecins_proches,
        'laboratoires_proches': laboratoires_proches,
        'pharmacies_proches': pharmacies_proches,
        'user_lat': user_lat,
        'user_lng': user_lng
    })

def analyze_speciality(text):
    """
    Analyse le texte pour déterminer la spécialité médicale appropriée.
    À améliorer avec une vraie analyse IA.
    """
    # Mapping simple de mots-clés vers spécialités
    specialites = {
        'cardiaque': 'Cardiologie',
        'coeur': 'Cardiologie',
        'poumon': 'Pneumologie',
        'respiration': 'Pneumologie',
        'peau': 'Dermatologie',
        'dermatologie': 'Dermatologie',
        'os': 'Orthopédie',
        'articulation': 'Orthopédie',
        'dent': 'Dentiste',
        'dentaire': 'Dentiste',
        'yeux': 'Ophtalmologie',
        'vision': 'Ophtalmologie',
        'enfant': 'Pédiatrie',
        'bebe': 'Pédiatrie',
        'femme': 'Gynécologie',
        'grossesse': 'Gynécologie'
    }
    
    text = text.lower()
    for keyword, specialite in specialites.items():
        if keyword in text:
            return specialite
    
    return 'Médecine générale'  # Spécialité par défaut

@login_required
def medecin_list(request):
    medecins = Medecin.objects.all()
    return render(request, 'medecin/list.html', {'medecins': medecins})

@login_required
def medecin_detail(request, pk):
    medecin = get_object_or_404(Medecin, pk=pk)
    rendez_vous = RendezVous.objects.filter(medecin=medecin)
    return render(request, 'medecin/detail.html', {
        'medecin': medecin,
        'rendez_vous': rendez_vous
    })

@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'patient/list.html', {'patients': patients})

@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    rendez_vous = RendezVous.objects.filter(patient=patient)
    return render(request, 'patient/detail.html', {
        'patient': patient,
        'rendez_vous': rendez_vous
    })

@login_required
def rendez_vous_list(request):
    rendez_vous = RendezVous.objects.all().order_by('-date_heure')
    return render(request, 'rendez_vous/list.html', {'rendez_vous': rendez_vous})

@login_required
def laboratoire_list(request):
    laboratoires = Laboratoire.objects.all()
    return render(request, 'laboratoire/list.html', {'laboratoires': laboratoires})

@login_required
def laboratoire_detail(request, pk):
    laboratoire = get_object_or_404(Laboratoire, pk=pk)
    return render(request, 'laboratoire/detail.html', {'laboratoire': laboratoire})

@login_required
def pharmacien_list(request):
    pharmaciens = Pharmacien.objects.all()
    return render(request, 'pharmacien/list.html', {'pharmaciens': pharmaciens})

@login_required
def pharmacien_detail(request, pk):
    pharmacien = get_object_or_404(Pharmacien, pk=pk)
    return render(request, 'pharmacien/detail.html', {'pharmacien': pharmacien})

def medecin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Vérifier que l'utilisateur est bien un médecin
            try:
                medecin = Medecin.objects.get(user=user)
                if medecin.is_validated_by_admin and medecin.user.is_active:
                    login(request, user)
                    return redirect('medecin_dashboard')
                else:
                    messages.error(request, "Votre compte est en attente de validation par l'administrateur.")
            except Medecin.DoesNotExist:
                messages.error(request, "Ce compte n'est pas un médecin.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'medecin/login.html')

@login_required
def medecin_dashboard(request):
    if not hasattr(request.user, 'medecin'):
        return redirect('home')
    
    medecin = request.user.medecin
    
    # Récupérer les rendez-vous du jour
    today = timezone.now().date()
    rdv_today = RendezVous.objects.filter(
        medecin=medecin,
        date_heure__date=today
    ).order_by('date_heure')
    
    # Récupérer les rendez-vous en attente
    rdv_en_attente = RendezVous.objects.filter(
        medecin=medecin,
        statut='en_attente',
        date_heure__gte=timezone.now()
    ).order_by('date_heure')
    
    # Récupérer tous les rendez-vous à venir
    tous_rdv = RendezVous.objects.filter(
        medecin=medecin,
        date_heure__gte=timezone.now()
    ).order_by('date_heure')
    
    # Compter le nombre de patients
    nb_patients = Patient.objects.filter(
        rendezvous__medecin=medecin
    ).distinct().count()
    
    context = {
        'medecin': medecin,
        'nb_rdv_today': rdv_today.count(),
        'nb_patients': nb_patients,
        'rdv_en_attente': rdv_en_attente,
        'tous_rdv': tous_rdv,
    }
    
    return render(request, 'medecin/dashboard.html', context)

@login_required
def update_rdv_status(request, rdv_id):
    if request.method == 'POST':
        rdv = get_object_or_404(RendezVous, id=rdv_id, medecin=request.user.medecin)
        new_status = request.POST.get('status')
        
        if new_status in ['confirme', 'annule']:
            rdv.statut = new_status
            rdv.save()
            
            # Envoyer un message au patient
            if new_status == 'confirme':
                messages.success(request, f"Le rendez-vous du {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été confirmé.")
            else:
                messages.info(request, f"Le rendez-vous du {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été annulé.")
                
        return redirect('medecin_dashboard')
    
    return redirect('medecin_dashboard')

def medecin_register(request):
    if request.method == 'POST':
        # Récupération des données du formulaire
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        specialite = request.POST.get('specialite')
        numero_ordre = request.POST.get('numero_ordre')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        email_professionnel = request.POST.get('email_professionnel')
        tarif = request.POST.get('tarif', 0)
        photo = request.FILES.get('photo')

        try:
            # Vérifier si l'email existe déjà
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Cet email est déjà utilisé.')
                return render(request, 'medecin/register.html')

            # Création de l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=False  # Le compte est désactivé jusqu'à validation
            )

            # Création du profil médecin
            medecin = Medecin.objects.create(
                user=user,
                specialite=specialite,
                numero_ordre=numero_ordre,
                telephone=telephone,
                adresse=adresse,
                email_professionnel=email_professionnel,
                tarif=tarif,
                photo=photo,
                is_validated_by_admin=False,  # En attente de validation par l'admin
                is_email_verified=False  # Email non vérifié
            )

            # Envoi de l'email à l'admin pour validation
            medecin.send_admin_approval_email()

            messages.success(request, 'Votre inscription a été soumise avec succès. Vous recevrez un email une fois votre compte validé par l\'administrateur.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'inscription : {str(e)}')
            return render(request, 'medecin/register.html')

    return render(request, 'medecin/register.html')

def patient_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                patient = Patient.objects.get(user=user)
                login(request, user)
                return redirect('patient_dashboard')
            except Patient.DoesNotExist:
                messages.error(request, "Ce compte n'est pas un patient.")
                return redirect('login')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            return redirect('login')
    return render(request, 'patient/login.html')

@login_required
def patient_dashboard(request):
    if not hasattr(request.user, 'patient'):
        messages.error(request, "Accès non autorisé. Vous devez être un patient pour accéder à cette page.")
        return redirect('home')
    
    # Récupérer les professionnels de santé validés
    medecins = list(Medecin.objects.filter(is_validated_by_admin=True).values(
        'id', 'specialite', 'adresse', 'telephone', 'latitude', 'longitude'
    ))
    pharmacies = list(Pharmacien.objects.filter(is_validated_by_admin=True).values(
        'id', 'adresse', 'telephone', 'latitude', 'longitude'
    ))
    laboratoires = list(Laboratoire.objects.filter(is_validated_by_admin=True).values(
        'id', 'adresse', 'telephone', 'latitude', 'longitude'
    ))
    
    # Récupérer l'historique des conversations
    chat_history = ChatMessage.objects.filter(patient=request.user.patient).order_by('created_at')
    
    # Formater les données pour le JavaScript
    medecins_data = [{
        'id': m['id'],
        'type': 'medecin',
        'specialite': m['specialite'],
        'adresse': m['adresse'],
        'telephone': m['telephone'],
        'latitude': float(m['latitude']) if m['latitude'] else None,
        'longitude': float(m['longitude']) if m['longitude'] else None
    } for m in medecins]
    
    pharmacies_data = [{
        'id': p['id'],
        'type': 'pharmacie',
        'adresse': p['adresse'],
        'telephone': p['telephone'],
        'latitude': float(p['latitude']) if p['latitude'] else None,
        'longitude': float(p['longitude']) if p['longitude'] else None
    } for p in pharmacies]
    
    laboratoires_data = [{
        'id': l['id'],
        'type': 'laboratoire',
        'adresse': l['adresse'],
        'telephone': l['telephone'],
        'latitude': float(l['latitude']) if l['latitude'] else None,
        'longitude': float(l['longitude']) if l['longitude'] else None
    } for l in laboratoires]
    
    context = {
        'medecins': medecins_data,
        'pharmacies': pharmacies_data,
        'laboratoires': laboratoires_data,
        'chat_history': chat_history,
        'patient': request.user.patient
    }
    
    return render(request, 'patient/dashboard.html', context)

def patient_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        date_naissance = request.POST.get('date_naissance')
        sexe = request.POST.get('sexe')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        groupe_sanguin = request.POST.get('groupe_sanguin')
        antecedents_medicaux = request.POST.get('antecedents_medicaux')
        
        # Vérifier si le username existe déjà
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, 'patient/register.html')
            
        try:
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_active=True
            )
            
            # Créer le profil patient
            Patient.objects.create(
                user=user,
                date_naissance=date_naissance,
                sexe=sexe,
                telephone=telephone,
                adresse=adresse,
                groupe_sanguin=groupe_sanguin,
                antecedents_medicaux=antecedents_medicaux
            )
            
            # Connecter automatiquement l'utilisateur
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Compte créé avec succès. Bienvenue sur votre espace patient !")
                return redirect('patient_dashboard')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de l'inscription : {str(e)}")
            return render(request, 'patient/register.html')
            
    return render(request, 'patient/register.html')

def laboratoire_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            from .models import Laboratoire
            try:
                laboratoire = Laboratoire.objects.get(user=user)
                login(request, user)
                return redirect('laboratoire_dashboard')
            except Laboratoire.DoesNotExist:
                messages.error(request, "Ce compte n'est pas un laboratoire.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'laboratoire/login.html')

@login_required
def laboratoire_dashboard(request):
    return render(request, 'laboratoire/dashboard.html')

def laboratoire_register(request):
    if request.method == 'POST':
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=request.POST['email'],
            email=request.POST['email'],
            password=request.POST['password'],
            first_name=request.POST['nom']
        )
        
        # Créer le laboratoire
        laboratoire = Laboratoire.objects.create(
            user=user,
            nom=request.POST['nom'],
            telephone=request.POST['telephone'],
            adresse=request.POST['adresse'],
            email_professionnel=request.POST['email']
        )
        
        # Envoyer l'email de vérification
        laboratoire.send_verification_email()
        
        messages.success(request, 'Inscription réussie. Veuillez vérifier votre email.')
        return redirect('login')
    
    return render(request, 'laboratoire/register.html')

def pharmacien_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            from .models import Pharmacien
            try:
                pharmacien = Pharmacien.objects.get(user=user)
                login(request, user)
                return redirect('pharmacien_dashboard')
            except Pharmacien.DoesNotExist:
                messages.error(request, "Ce compte n'est pas un pharmacien.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'pharmacien/login.html')

@login_required
def pharmacien_dashboard(request):
    return render(request, 'pharmacien/dashboard.html')

def pharmacien_register(request):
    if request.method == 'POST':
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=request.POST['email'],
            email=request.POST['email'],
            password=request.POST['password'],
            first_name=request.POST['nom_officine']
        )
        
        # Créer le pharmacien
        pharmacien = Pharmacien.objects.create(
            user=user,
            nom_officine=request.POST['nom_officine'],
            telephone=request.POST['telephone'],
            adresse=request.POST['adresse'],
            email_professionnel=request.POST['email']
        )
        
        # Envoyer l'email de vérification
        pharmacien.send_verification_email()
        
        messages.success(request, 'Inscription réussie. Veuillez vérifier votre email.')
        return redirect('login')
    
    return render(request, 'pharmacien/register.html')

def chat_medical(request):
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    chat_history = request.session['chat_history']
    
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            chat_history.append({"role": "user", "content": user_message})
            try:
                ai_message = call_rapidapi_chat(chat_history)
                chat_history.append({"role": "assistant", "content": ai_message})
            except Exception as e:
                ai_message = f"Erreur lors de l'analyse : {e}"
                chat_history.append({"role": "assistant", "content": ai_message})
            request.session['chat_history'] = chat_history
    
    return render(request, 'chat.html', {'chat_history': chat_history})

@login_required
def take_appointment(request, medecin_id):
    medecin = get_object_or_404(Medecin, pk=medecin_id)
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        motif = request.POST.get('motif')
        notes = request.POST.get('notes', '')
        
        try:
            # Combiner la date et l'heure
            date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Vérifier si le créneau est disponible
            if RendezVous.objects.filter(
                medecin=medecin,
                date_heure=date_time,
                statut__in=['en_attente', 'confirme']
            ).exists():
                messages.error(request, "Ce créneau n'est plus disponible.")
                return redirect('take_appointment', medecin_id=medecin_id)
            
            # Créer le rendez-vous
            rendez_vous = RendezVous.objects.create(
                patient=request.user.patient,
                medecin=medecin,
                date_heure=date_time,
                motif=motif,
                notes=notes,
                statut='en_attente'
            )
            
            # Envoyer une notification au médecin
            messages.success(request, "Votre rendez-vous a été enregistré avec succès.")
            
            # Rediriger vers la page des rendez-vous du patient
            return redirect('mes_rendez_vous')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")
    
    return render(request, 'rendez_vous/take_appointment.html', {
        'medecin': medecin
    })

@login_required
def get_available_slots(request, medecin_id):
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Date requise'}, status=400)
    
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        medecin = get_object_or_404(Medecin, pk=medecin_id)
        
        # Récupérer les rendez-vous existants pour cette date
        existing_appointments = RendezVous.objects.filter(
            medecin=medecin,
            date_heure__date=date,
            statut__in=['en_attente', 'confirme']
        ).values_list('date_heure__time', flat=True)
        
        # Générer tous les créneaux possibles
        slots = []
        start_hour = 9
        end_hour = 18
        interval = 30  # minutes
        
        for hour in range(start_hour, end_hour):
            for minute in range(0, 60, interval):
                time = timezone.datetime.strptime(
                    f"{hour:02d}:{minute:02d}", "%H:%M"
                ).time()
                
                # Vérifier si le créneau est disponible
                is_available = time not in existing_appointments
                
                slots.append({
                    'time': time.strftime("%H:%M"),
                    'available': is_available
                })
        
        return JsonResponse({'slots': slots})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def cancel_appointment(request, rendez_vous_id):
    rendez_vous = get_object_or_404(RendezVous, pk=rendez_vous_id)
    
    # Vérifier que l'utilisateur est bien le patient concerné
    if request.user.patient != rendez_vous.patient:
        messages.error(request, "Vous n'êtes pas autorisé à annuler ce rendez-vous.")
        return redirect('patient_dashboard')
    
    if request.method == 'POST':
        rendez_vous.statut = 'annule'
        rendez_vous.save()
        messages.success(request, "Le rendez-vous a été annulé avec succès.")
        return redirect('patient_dashboard')
    
    return render(request, 'rendez_vous/cancel.html', {
        'rendez_vous': rendez_vous
    })

def ajouter_disponibilite(request):
    return render(request, 'medecin/ajouter_disponibilite.html')

def patients_list(request):
    medecin = request.user.medecin
    # Patients ayant eu un rendez-vous avec ce médecin
    patient_ids = RendezVous.objects.filter(medecin=medecin).values_list('patient', flat=True).distinct()
    patients = Patient.objects.filter(id__in=patient_ids)
    return render(request, 'medecin/patients_list.html', {'patients': patients})

def medecin_notes(request):
    medecin = request.user.medecin
    patient_ids = RendezVous.objects.filter(medecin=medecin).values_list('patient', flat=True).distinct()
    patients = Patient.objects.filter(id__in=patient_ids)
    # Simuler une liste de notes (à remplacer par un vrai modèle Note si besoin)
    notes = []
    if request.method == 'POST':
        # Ici, tu pourrais enregistrer la note dans un vrai modèle
        pass
    return render(request, 'medecin/notes.html', {'patients': patients, 'notes': notes})

def medecin_ordonnances(request):
    medecin = request.user.medecin
    patient_ids = RendezVous.objects.filter(medecin=medecin).values_list('patient', flat=True).distinct()
    patients = Patient.objects.filter(id__in=patient_ids)
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        medicaments = request.POST.get('medicaments')
        if patient_id and medicaments:
            Ordonnance.objects.create(medecin=medecin, patient_id=patient_id, medicaments=medicaments)
    ordonnances = Ordonnance.objects.filter(medecin=medecin).order_by('-created_at')
    return render(request, 'medecin/ordonnances.html', {'patients': patients, 'ordonnances': ordonnances})

def medecin_messages(request):
    medecin = request.user.medecin
    patient_ids = RendezVous.objects.filter(medecin=medecin).values_list('patient', flat=True).distinct()
    patients = Patient.objects.filter(id__in=patient_ids)
    from .models import Message
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        contenu = request.POST.get('message')
        if patient_id and contenu:
            Message.objects.create(expediteur=request.user, destinataire=Patient.objects.get(pk=patient_id).user, contenu=contenu)
    # Afficher tous les messages envoyés ou reçus par le médecin
    messages = Message.objects.filter(models.Q(expediteur=request.user) | models.Q(destinataire=request.user)).order_by('-created_at')
    return render(request, 'medecin/messages.html', {'patients': patients, 'messages': messages})

def contacts_labo_pharma(request):
    laboratoires = Laboratoire.objects.all()
    pharmacies = Pharmacien.objects.all()
    return render(request, 'medecin/contacts.html', {'laboratoires': laboratoires, 'pharmacies': pharmacies})

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('/')  # Redirection vers la page racine

def disponibilites_medecin(request):
    medecin = request.user.medecin
    from .models import Disponibilite
    if request.method == 'POST':
        date = request.POST.get('date')
        heure_debut = request.POST.get('heure_debut')
        heure_fin = request.POST.get('heure_fin')
        if date and heure_debut and heure_fin:
            Disponibilite.objects.create(medecin=medecin, date=date, heure_debut=heure_debut, heure_fin=heure_fin)
    disponibilites = Disponibilite.objects.filter(medecin=medecin).order_by('date', 'heure_debut')
    return render(request, 'medecin/disponibilites.html', {'disponibilites': disponibilites})

def consultations_en_ligne(request):
    medecin = request.user.medecin
    rdvs = RendezVous.objects.filter(medecin=medecin, date_heure__gte=timezone.now()).order_by('date_heure')
    return render(request, 'medecin/consultations_en_ligne.html', {'rdvs': rdvs})

@login_required
def prendre_rdv(request):
    # Récupérer tous les médecins validés et actifs avec leurs informations complètes
    medecins = Medecin.objects.filter(
        is_validated_by_admin=True,
        user__is_active=True
    ).select_related('user')  # Optimisation de la requête
    
    return render(request, 'patient/prendre_rdv.html', {
        'medecins': medecins,
        'today': timezone.now().date()  # Pour la validation de la date minimale
    })

@login_required
def mes_rendez_vous(request):
    if not hasattr(request.user, 'patient'):
        messages.error(request, "Accès non autorisé.")
        return redirect('home')
    
    rendez_vous = RendezVous.objects.filter(
        patient=request.user.patient
    ).select_related(
        'medecin',
        'medecin__user'
    ).order_by('-date_heure')
    
    return render(request, 'patient/mes_rendez_vous.html', {
        'rendez_vous': rendez_vous
    })

@login_required
def mes_prescriptions(request):
    return render(request, 'patient/mes_prescriptions.html')

@login_required
def resultats_tests(request):
    return render(request, 'patient/resultats_tests.html')

@login_required
def messagerie_patient(request):
    return render(request, 'patient/messagerie_patient.html')

@login_required
def historique_consultations(request):
    return render(request, 'patient/historique_consultations.html')

@login_required
def profil_patient(request):
    return render(request, 'patient/profil_patient.html')

# LABORATOIRE
@login_required
def commandes_tests(request):
    return render(request, 'laboratoire/commandes_tests.html')

@login_required
def resultats_a_soumettre(request):
    return render(request, 'laboratoire/resultats_a_soumettre.html')

@login_required
def messagerie_laboratoire(request):
    return render(request, 'laboratoire/messagerie_laboratoire.html')

@login_required
def notifications_laboratoire(request):
    return render(request, 'laboratoire/notifications_laboratoire.html')

@login_required
def profil_laboratoire(request):
    return render(request, 'laboratoire/profil_laboratoire.html')

# PHARMACIEN
@login_required
def prescriptions_a_traiter(request):
    return render(request, 'pharmacien/prescriptions_a_traiter.html')

@login_required
def stock_medicaments(request):
    return render(request, 'pharmacien/stock_medicaments.html')

@login_required
def messagerie_pharmacien(request):
    return render(request, 'pharmacien/messagerie_pharmacien.html')

@login_required
def notifications_pharmacien(request):
    return render(request, 'pharmacien/notifications_pharmacien.html')

@login_required
def profil_pharmacien(request):
    return render(request, 'pharmacien/profil_pharmacien.html')

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Récupérer tous les utilisateurs en attente de validation
    medecins = Medecin.objects.filter(is_email_verified=True, is_validated_by_admin=False)
    laboratoires = Laboratoire.objects.filter(is_email_verified=True, is_validated_by_admin=False)
    pharmaciens = Pharmacien.objects.filter(is_email_verified=True, is_validated_by_admin=False)
    
    context = {
        'medecins': medecins,
        'laboratoires': laboratoires,
        'pharmaciens': pharmaciens,
        'total_pending': medecins.count() + laboratoires.count() + pharmaciens.count()
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def approve_user(request, user_type, user_id):
    if user_type == 'medecin':
        user = get_object_or_404(Medecin, id=user_id)
    elif user_type == 'laboratoire':
        user = get_object_or_404(Laboratoire, id=user_id)
    elif user_type == 'pharmacien':
        user = get_object_or_404(Pharmacien, id=user_id)
    else:
        messages.error(request, 'Type d\'utilisateur invalide')
        return redirect('admin_dashboard')
    
    try:
        # Envoyer l'email de confirmation AVANT d'activer le compte
        user.send_approval_status_email(approved=True)
        
        # Activer le compte utilisateur
        user.user.is_active = True
        user.user.save()
        
        # Marquer comme validé par l'admin
        user.is_validated_by_admin = True
        user.save()
        
        messages.success(request, f'Utilisateur {user_type} approuvé avec succès. Un email de confirmation a été envoyé.')
        return redirect('admin_dashboard')
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'approbation : {str(e)}')
        return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def reject_user(request, user_type, user_id):
    if user_type == 'medecin':
        user = get_object_or_404(Medecin, id=user_id)
    elif user_type == 'laboratoire':
        user = get_object_or_404(Laboratoire, id=user_id)
    elif user_type == 'pharmacien':
        user = get_object_or_404(Pharmacien, id=user_id)
    else:
        messages.error(request, 'Type d\'utilisateur invalide')
        return redirect('admin_dashboard')
    
    try:
        # Envoyer l'email de rejet AVANT de supprimer le compte
        user.send_approval_status_email(approved=False)
        
        # Supprimer l'utilisateur et son profil
        user.user.delete()
        
        messages.success(request, f'Utilisateur {user_type} rejeté avec succès. Un email de notification a été envoyé.')
        return redirect('admin_dashboard')
    except Exception as e:
        messages.error(request, f'Erreur lors du rejet : {str(e)}')
        return redirect('admin_dashboard')

@login_required
def chat_with_ai(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            
            if not message:
                return JsonResponse({'error': 'Message vide'}, status=400)
            
            # Appeler l'API RapidAPI
            conn = http.client.HTTPSConnection("chatgpt-42.p.rapidapi.com")
            
            # Préparation du message
            prompt = f"""Tu es un assistant médical virtuel. 
            Réponds à la question du patient de manière professionnelle et informative.
            Si la question concerne des symptômes ou des problèmes de santé :
            1. Fournis une analyse préliminaire
            2. Donne des conseils généraux
            3. Recommande de consulter un médecin si nécessaire
            
            IMPORTANT : Précise bien que tu n'es pas un médecin et que tes conseils ne remplacent pas une consultation médicale.
            
            Question du patient : {message}"""
            
            payload = json.dumps({
                "text": prompt
            })
            
            headers = {
                'x-rapidapi-key': '683d0e7fe7mshcbd64d813ffc274p1e6188jsn473850d255fa',
                'x-rapidapi-host': 'chatgpt-42.p.rapidapi.com',
                'Content-Type': 'application/json'
            }
            
            conn.request("POST", "/aitohuman", payload, headers)
            res = conn.getresponse()
            data = res.read()
            result = json.loads(data.decode("utf-8"))
            
            # Traitement de la réponse
            if "result" in result:
                if isinstance(result["result"], str):
                    response = result["result"].strip()
                elif isinstance(result["result"], list) and result["result"]:
                    response = result["result"][0].strip()
                else:
                    response = "Désolé, je n'ai pas pu traiter votre demande correctement."
            else:
                response = "Désolé, je n'ai pas pu traiter votre demande correctement."
            
            # Sauvegarder l'historique dans la session
            chat_history = request.session.get('chat_history', [])
            chat_history.append({
                'role': 'user',
                'content': message
            })
            chat_history.append({
                'role': 'assistant',
                'content': response
            })
            request.session['chat_history'] = chat_history[-10:]  # Garder les 10 derniers messages
            
            return JsonResponse({'response': response})
            
        except Exception as e:
            print(f"Erreur dans chat_with_ai: {str(e)}")  # Pour le débogage
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def visitor_page(request):
    """Vue pour la page d'accueil des visiteurs"""
    response = None
    symptoms = ''
    duration = ''
    
    if request.method == 'POST':
        symptoms = request.POST.get('symptoms', '')
        duration = request.POST.get('duration', '')
        
        if symptoms:
            try:
                # Configuration de l'API RapidAPI
                conn = http.client.HTTPSConnection(settings.RAPIDAPI_HOST)
                
                # Préparation du message
                prompt = f"""Tu es un assistant médical virtuel. 
                Analyse les symptômes suivants et fournis :
                1. Une analyse préliminaire des symptômes
                2. Des conseils généraux
                3. Des recommandations sur la nécessité de consulter un médecin
                
                Symptômes : {symptoms}
                Durée : {duration}
                
                IMPORTANT : Précise bien que tu n'es pas un médecin et que tes conseils ne remplacent pas une consultation médicale."""
                
                payload = json.dumps({
                    "text": prompt
                })
                
                headers = {
                    'x-rapidapi-key': settings.RAPIDAPI_KEY,
                    'x-rapidapi-host': settings.RAPIDAPI_HOST,
                    'Content-Type': 'application/json'
                }
                
                print("Envoi de la requête à l'API...")
                print(f"Headers : {headers}")
                print(f"Payload : {payload}")
                
                conn.request("POST", "/aitohuman", payload, headers)
                res = conn.getresponse()
                data = res.read()
                print(f"Réponse brute de l'API : {data.decode('utf-8')}")
                
                if res.status != 200:
                    print(f"Erreur HTTP : {res.status} {res.reason}")
                    response = "Désolé, une erreur s'est produite lors de l'analyse. Veuillez réessayer plus tard."
                    return render(request, 'visitor.html', {
                        'response': response,
                        'symptoms': symptoms,
                        'duration': duration
                    })
                
                try:
                    result = json.loads(data.decode("utf-8"))
                    print(f"Réponse décodée : {result}")
                    
                    # Traitement de la réponse
                    if "result" in result:
                        if isinstance(result["result"], str):
                            response = result["result"].strip()
                        elif isinstance(result["result"], list) and result["result"]:
                            response = result["result"][0].strip()
                        else:
                            print(f"Format de réponse non reconnu : {result}")
                            response = "Désolé, je n'ai pas pu analyser vos symptômes correctement."
                    else:
                        print(f"Pas de 'result' dans la réponse : {result}")
                        response = "Désolé, je n'ai pas pu analyser vos symptômes correctement."
                        
                except json.JSONDecodeError as e:
                    print(f"Erreur de décodage JSON : {str(e)}")
                    print(f"Données reçues : {data.decode('utf-8')}")
                    response = "Désolé, une erreur s'est produite lors de l'analyse. Veuillez réessayer."
                    
            except Exception as e:
                print(f"Erreur lors de l'analyse : {str(e)}")
                response = "Désolé, une erreur s'est produite lors de l'analyse. Veuillez réessayer."
    
    return render(request, 'visitor.html', {
        'response': response,
        'symptoms': symptoms,
        'duration': duration
    })

@login_required
@require_POST
def patient_chat(request):
    if not hasattr(request.user, 'patient'):
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    try:
        data = json.loads(request.body)
        message = data.get('message')
        
        if not message:
            return JsonResponse({'error': 'Message vide'}, status=400)
        
        # Sauvegarder le message du patient
        patient = request.user.patient
        ChatMessage.objects.create(
            patient=patient,
            message=message,
            is_from_ai=False
        )
        
        # Appeler l'API ChatGPT
        conn = http.client.HTTPSConnection("chatgpt-42.p.rapidapi.com")
        
        # Préparation du message
        prompt = f"""Tu es un assistant médical virtuel. 
        Réponds à la question du patient de manière professionnelle et informative.
        Si la question concerne des symptômes ou des problèmes de santé :
        1. Fournis une analyse préliminaire
        2. Donne des conseils généraux
        3. Recommande de consulter un médecin si nécessaire
        
        IMPORTANT : Précise bien que tu n'es pas un médecin et que tes conseils ne remplacent pas une consultation médicale.
        
        Question du patient : {message}"""
        
        payload = json.dumps({
            "text": prompt
        })
        
        headers = {
            'x-rapidapi-key': settings.OPENAI_API_KEY,
            'x-rapidapi-host': 'chatgpt-42.p.rapidapi.com',
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/aitohuman", payload, headers)
        res = conn.getresponse()
        data = res.read()
        result = json.loads(data.decode("utf-8"))
        
        # Traitement de la réponse
        if "result" in result:
            if isinstance(result["result"], str):
                response = result["result"].strip()
            elif isinstance(result["result"], list) and result["result"]:
                response = result["result"][0].strip()
            else:
                response = "Désolé, je n'ai pas pu traiter votre demande correctement."
        else:
            response = "Désolé, je n'ai pas pu traiter votre demande correctement."
        
        # Sauvegarder la réponse de l'IA
        ChatMessage.objects.create(
            patient=patient,
            message=response,
            is_from_ai=True
        )
        
        return JsonResponse({'response': response})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def medecin_chat(request):
    if not hasattr(request.user, 'medecin'):
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            
            if not message:
                return JsonResponse({'error': 'Message vide'}, status=400)
            
            # Sauvegarder le message du médecin
            medecin = request.user.medecin
            ChatMessage.objects.create(
                medecin=medecin,
                message=message,
                is_from_ai=False
            )
            
            # Appeler l'API ChatGPT
            conn = http.client.HTTPSConnection("chatgpt-42.p.rapidapi.com")
            
            # Préparation du message
            prompt = f"""Tu es un assistant médical virtuel spécialisé pour les médecins. 
            Réponds aux questions du médecin de manière professionnelle et technique.
            Si la question concerne un cas médical :
            1. Fournis une analyse détaillée
            2. Suggère des protocoles de traitement possibles
            3. Mentionne les dernières recommandations médicales pertinentes
            4. Cite des sources médicales fiables si nécessaire
            
            Question du médecin : {message}"""
            
            payload = json.dumps({
                "text": prompt
            })
            
            headers = {
                'x-rapidapi-key': settings.OPENAI_API_KEY,
                'x-rapidapi-host': 'chatgpt-42.p.rapidapi.com',
                'Content-Type': 'application/json'
            }
            
            conn.request("POST", "/aitohuman", payload, headers)
            res = conn.getresponse()
            data = res.read()
            result = json.loads(data.decode("utf-8"))
            
            # Sauvegarder la réponse de l'IA
            ai_response = result.get('response', 'Désolé, je ne peux pas répondre pour le moment.')
            ChatMessage.objects.create(
                medecin=medecin,
                message=ai_response,
                is_from_ai=True
            )
            
            return JsonResponse({'response': ai_response})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Récupérer l'historique des conversations
    chat_history = ChatMessage.objects.filter(medecin=request.user.medecin).order_by('created_at')
    
    return render(request, 'medecin/chat.html', {'chat_history': chat_history})

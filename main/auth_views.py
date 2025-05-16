from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Medecin, Patient, Laboratoire, Pharmacien
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils.crypto import get_random_string

def register_medecin(request):
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            specialite = request.POST.get('specialite')
            numero_ordre = request.POST.get('numero_ordre')
            telephone = request.POST.get('telephone')
            adresse = request.POST.get('adresse')
            email_professionnel = request.POST.get('email_professionnel')
            tarif = request.POST.get('tarif')
            photo = request.FILES.get('photo')

            # Récupération des horaires
            horaires = {
                'lundi': {
                    'debut': request.POST.get('horaires_lundi_debut'),
                    'fin': request.POST.get('horaires_lundi_fin')
                },
                'mardi': {
                    'debut': request.POST.get('horaires_mardi_debut'),
                    'fin': request.POST.get('horaires_mardi_fin')
                },
                'mercredi': {
                    'debut': request.POST.get('horaires_mercredi_debut'),
                    'fin': request.POST.get('horaires_mercredi_fin')
                },
                'jeudi': {
                    'debut': request.POST.get('horaires_jeudi_debut'),
                    'fin': request.POST.get('horaires_jeudi_fin')
                },
                'vendredi': {
                    'debut': request.POST.get('horaires_vendredi_debut'),
                    'fin': request.POST.get('horaires_vendredi_fin')
                },
                'samedi': {
                    'debut': request.POST.get('horaires_samedi_debut'),
                    'fin': request.POST.get('horaires_samedi_fin')
                }
            }

            # Récupération des services
            services = request.POST.getlist('services')

            # Vérifier si l'email existe déjà
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Cet email est déjà utilisé.')
                return render(request, 'registration/register_medecin.html')

            # Création de l'utilisateur avec l'email comme nom d'utilisateur
            user = User.objects.create_user(
                username=email,
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
                services=services,
                horaires=horaires,
                is_email_verified=True,  # Email vérifié directement
                is_validated_by_admin=False  # En attente de validation par l'admin
            )

            # Envoyer un email à l'admin pour validation
            medecin.send_admin_approval_email()

            messages.success(request, 'Votre inscription a été soumise avec succès. Vous recevrez un email une fois votre compte validé par l\'administrateur.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'inscription : {str(e)}')
            return render(request, 'registration/register_medecin.html')

    return render(request, 'registration/register_medecin.html')

def register_patient(request):
    if request.method == 'POST':
        # Récupération des données du formulaire
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        date_naissance = request.POST.get('date_naissance')
        sexe = request.POST.get('sexe')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        groupe_sanguin = request.POST.get('groupe_sanguin')

        # Création de l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True  # Le compte est activé immédiatement pour les patients
        )

        # Création du profil patient
        Patient.objects.create(
            user=user,
            date_naissance=date_naissance,
            sexe=sexe,
            telephone=telephone,
            adresse=adresse,
            groupe_sanguin=groupe_sanguin
        )

        messages.success(request, 'Votre inscription a été effectuée avec succès. Vous pouvez maintenant vous connecter.')
        return redirect('login')

    return render(request, 'registration/register_patient.html')

def register_laboratoire(request):
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            email = request.POST.get('email')
            password = request.POST.get('password')
            nom = request.POST.get('nom')
            telephone = request.POST.get('telephone')
            adresse = request.POST.get('adresse')
            email_professionnel = request.POST.get('email_professionnel')
            numero_agrement = request.POST.get('numero_agrement')

            # Récupération des horaires
            horaires = {
                'lundi': {
                    'debut': request.POST.get('horaires_lundi_debut'),
                    'fin': request.POST.get('horaires_lundi_fin')
                },
                'mardi': {
                    'debut': request.POST.get('horaires_mardi_debut'),
                    'fin': request.POST.get('horaires_mardi_fin')
                },
                'mercredi': {
                    'debut': request.POST.get('horaires_mercredi_debut'),
                    'fin': request.POST.get('horaires_mercredi_fin')
                },
                'jeudi': {
                    'debut': request.POST.get('horaires_jeudi_debut'),
                    'fin': request.POST.get('horaires_jeudi_fin')
                },
                'vendredi': {
                    'debut': request.POST.get('horaires_vendredi_debut'),
                    'fin': request.POST.get('horaires_vendredi_fin')
                },
                'samedi': {
                    'debut': request.POST.get('horaires_samedi_debut'),
                    'fin': request.POST.get('horaires_samedi_fin')
                }
            }

            # Récupération des services
            services = request.POST.getlist('services')

            # Vérifier si l'email existe déjà
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Cet email est déjà utilisé.')
                return render(request, 'registration/register_laboratoire.html')

            # Création de l'utilisateur
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                is_active=False
            )

            # Création du profil laboratoire
            laboratoire = Laboratoire.objects.create(
                user=user,
                nom=nom,
                telephone=telephone,
                adresse=adresse,
                email_professionnel=email_professionnel,
                numero_agrement=numero_agrement,
                horaires=horaires,
                services=services,
                is_email_verified=True,  # Email vérifié directement
                is_validated_by_admin=False  # En attente de validation par l'admin
            )

            # Envoyer un email à l'admin pour validation
            laboratoire.send_admin_approval_email()

            messages.success(request, 'Votre inscription a été soumise avec succès. Vous recevrez un email une fois votre compte validé par l\'administrateur.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'inscription : {str(e)}')
            return render(request, 'registration/register_laboratoire.html')

    return render(request, 'registration/register_laboratoire.html')

def register_pharmacien(request):
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            email = request.POST.get('email')
            password = request.POST.get('password')
            nom_officine = request.POST.get('nom_officine')
            telephone = request.POST.get('telephone')
            adresse = request.POST.get('adresse')
            email_professionnel = request.POST.get('email_professionnel')
            numero_ordre = request.POST.get('numero_ordre')

            # Récupération des horaires
            horaires = {
                'lundi': {
                    'debut': request.POST.get('horaires_lundi_debut'),
                    'fin': request.POST.get('horaires_lundi_fin')
                },
                'mardi': {
                    'debut': request.POST.get('horaires_mardi_debut'),
                    'fin': request.POST.get('horaires_mardi_fin')
                },
                'mercredi': {
                    'debut': request.POST.get('horaires_mercredi_debut'),
                    'fin': request.POST.get('horaires_mercredi_fin')
                },
                'jeudi': {
                    'debut': request.POST.get('horaires_jeudi_debut'),
                    'fin': request.POST.get('horaires_jeudi_fin')
                },
                'vendredi': {
                    'debut': request.POST.get('horaires_vendredi_debut'),
                    'fin': request.POST.get('horaires_vendredi_fin')
                },
                'samedi': {
                    'debut': request.POST.get('horaires_samedi_debut'),
                    'fin': request.POST.get('horaires_samedi_fin')
                }
            }

            # Récupération des services
            services = request.POST.getlist('services')

            # Vérifier si l'email existe déjà
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Cet email est déjà utilisé.')
                return render(request, 'registration/register_pharmacien.html')

            # Création de l'utilisateur
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                is_active=False
            )

            # Création du profil pharmacien
            pharmacien = Pharmacien.objects.create(
                user=user,
                nom_officine=nom_officine,
                telephone=telephone,
                adresse=adresse,
                email_professionnel=email_professionnel,
                numero_ordre=numero_ordre,
                horaires=horaires,
                services=services,
                is_email_verified=True,  # Email vérifié directement
                is_validated_by_admin=False  # En attente de validation par l'admin
            )

            # Envoyer un email à l'admin pour validation
            pharmacien.send_admin_approval_email()

            messages.success(request, 'Votre inscription a été soumise avec succès. Vous recevrez un email une fois votre compte validé par l\'administrateur.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'inscription : {str(e)}')
            return render(request, 'registration/register_pharmacien.html')

    return render(request, 'registration/register_pharmacien.html')

@staff_member_required
def approve_user(request, user_type, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    if user_type == 'medecin':
        user = get_object_or_404(Medecin, id=user_id)
    elif user_type == 'laboratoire':
        user = get_object_or_404(Laboratoire, id=user_id)
    elif user_type == 'pharmacien':
        user = get_object_or_404(Pharmacien, id=user_id)
    else:
        return JsonResponse({'error': 'Type d\'utilisateur invalide'}, status=400)

    try:
        # Envoyer l'email de confirmation AVANT d'activer le compte
        user.send_approval_status_email(approved=True)
        
        # Activer le compte utilisateur
        user.user.is_active = True
        user.user.save()
        
        # Marquer comme validé par l'admin
        user.is_validated_by_admin = True
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Utilisateur {user_type} approuvé avec succès. Un email de confirmation a été envoyé.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de l\'approbation : {str(e)}'
        }, status=500)

@staff_member_required
def reject_user(request, user_type, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
    if user_type == 'medecin':
        user = get_object_or_404(Medecin, id=user_id)
    elif user_type == 'laboratoire':
        user = get_object_or_404(Laboratoire, id=user_id)
    elif user_type == 'pharmacien':
        user = get_object_or_404(Pharmacien, id=user_id)
    else:
        return JsonResponse({'error': 'Type d\'utilisateur invalide'}, status=400)

    try:
        # Envoyer l'email de rejet AVANT de supprimer le compte
        user.send_approval_status_email(approved=False)
        
        # Supprimer l'utilisateur et son profil
        user.user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Utilisateur {user_type} rejeté avec succès. Un email de notification a été envoyé.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du rejet : {str(e)}'
        }, status=500) 
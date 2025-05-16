from django.contrib import admin
from .models import Medecin, Patient, RendezVous, Laboratoire, Pharmacien

@admin.register(Medecin)
class MedecinAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialite', 'numero_ordre', 'telephone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'numero_ordre')
    list_filter = ('specialite',)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_naissance', 'sexe', 'telephone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('sexe',)

@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin', 'date_heure', 'statut')
    search_fields = ('patient__user__username', 'medecin__user__username')
    list_filter = ('statut', 'date_heure')

@admin.register(Laboratoire)
class LaboratoireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'adresse')
    search_fields = ('nom',)

@admin.register(Pharmacien)
class PharmacienAdmin(admin.ModelAdmin):
    list_display = ('nom_officine', 'telephone', 'adresse')
    search_fields = ('nom_officine',)

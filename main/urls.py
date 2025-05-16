from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    path('', views.visitor_page, name='visitor_page'),
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('patient/chat/', views.patient_chat, name='patient_chat'),
    
    # Inscription
    path('register/medecin/', auth_views.register_medecin, name='register_medecin'),
    path('register/patient/', auth_views.register_patient, name='register_patient'),
    path('register/laboratoire/', auth_views.register_laboratoire, name='register_laboratoire'),
    path('register/pharmacien/', auth_views.register_pharmacien, name='register_pharmacien'),
    
    # Tableaux de bord
    path('medecin/dashboard/', views.medecin_dashboard, name='medecin_dashboard'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('laboratoire/dashboard/', views.laboratoire_dashboard, name='laboratoire_dashboard'),
    path('pharmacien/dashboard/', views.pharmacien_dashboard, name='pharmacien_dashboard'),
    
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/approve/<str:user_type>/<int:user_id>/', views.approve_user, name='approve_user'),
    path('admin/reject/<str:user_type>/<int:user_id>/', views.reject_user, name='reject_user'),
    
    # Médecins
    path('medecin/list/', views.medecin_list, name='medecin_list'),
    path('medecin/<int:pk>/', views.medecin_detail, name='medecin_detail'),
    path('medecin/patients/', views.patients_list, name='patients_list'),
    path('medecin/notes/', views.medecin_notes, name='medecin_notes'),
    path('medecin/ordonnances/', views.medecin_ordonnances, name='medecin_ordonnances'),
    path('medecin/messages/', views.medecin_messages, name='medecin_messages'),
    path('medecin/consultations/', views.consultations_en_ligne, name='consultations_en_ligne'),
    path('medecin/contacts/', views.contacts_labo_pharma, name='contacts_labo_pharma'),
    path('medecin/disponibilites/', views.disponibilites_medecin, name='disponibilites_medecin'),
    path('medecin/ajouter-disponibilite/', views.ajouter_disponibilite, name='ajouter_disponibilite'),
    
    # Patients
    path('patient/list/', views.patient_list, name='patient_list'),
    path('patient/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patient/rendez-vous/', views.mes_rendez_vous, name='mes_rendez_vous'),
    path('patient/prescriptions/', views.mes_prescriptions, name='mes_prescriptions'),
    path('patient/resultats/', views.resultats_tests, name='resultats_tests'),
    path('patient/messagerie/', views.messagerie_patient, name='messagerie_patient'),
    path('patient/historique/', views.historique_consultations, name='historique_consultations'),
    path('patient/profil/', views.profil_patient, name='profil_patient'),
    path('patient/prendre-rdv/', views.prendre_rdv, name='prendre_rdv'),
    
    # Laboratoires
    path('laboratoire/list/', views.laboratoire_list, name='laboratoire_list'),
    path('laboratoire/<int:pk>/', views.laboratoire_detail, name='laboratoire_detail'),
    path('laboratoire/commandes/', views.commandes_tests, name='commandes_tests'),
    path('laboratoire/resultats/', views.resultats_a_soumettre, name='resultats_a_soumettre'),
    path('laboratoire/messagerie/', views.messagerie_laboratoire, name='messagerie_laboratoire'),
    path('laboratoire/notifications/', views.notifications_laboratoire, name='notifications_laboratoire'),
    path('laboratoire/profil/', views.profil_laboratoire, name='profil_laboratoire'),
    
    # Pharmaciens
    path('pharmacien/list/', views.pharmacien_list, name='pharmacien_list'),
    path('pharmacien/<int:pk>/', views.pharmacien_detail, name='pharmacien_detail'),
    path('pharmacien/prescriptions/', views.prescriptions_a_traiter, name='prescriptions_a_traiter'),
    path('pharmacien/stock/', views.stock_medicaments, name='stock_medicaments'),
    path('pharmacien/messagerie/', views.messagerie_pharmacien, name='messagerie_pharmacien'),
    path('pharmacien/notifications/', views.notifications_pharmacien, name='notifications_pharmacien'),
    path('pharmacien/profil/', views.profil_pharmacien, name='profil_pharmacien'),
    
    # Rendez-vous
    path('rendez-vous/list/', views.rendez_vous_list, name='rendez_vous_list'),
    path('rendez-vous/mes-rendez-vous/', views.mes_rendez_vous, name='mes_rendez_vous'),
    path('rendez-vous/take/<int:medecin_id>/', views.take_appointment, name='take_appointment'),
    path('rendez-vous/cancel/<int:rendez_vous_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('rendez-vous/slots/<int:medecin_id>/', views.get_available_slots, name='get_available_slots'),
    
    # Chat
    path('chat/', views.chat_medical, name='chat_medical'),
    path('chat/ai/', views.chat_with_ai, name='chat_with_ai'),
] 
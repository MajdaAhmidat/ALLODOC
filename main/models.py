from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

class Medecin(models.Model):
    SPECIALITES = [
        ('generaliste', 'Médecin Généraliste'),
        ('pediatre', 'Pédiatre'),
        ('dermatologue', 'Dermatologue'),
        ('cardiologue', 'Cardiologue'),
        ('gynecologue', 'Gynécologue'),
        ('autre', 'Autre'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialite = models.CharField(max_length=100, default='generaliste')
    numero_ordre = models.CharField(max_length=50)
    telephone = models.CharField(max_length=20)
    adresse = models.CharField(max_length=200)
    email_professionnel = models.EmailField(unique=True, null=True, blank=True)
    is_validated_by_admin = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    horaires = models.JSONField(default=dict)
    tarif = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    services = models.JSONField(default=list)
    photo = models.ImageField(upload_to='medecins/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialite}"

    def send_admin_approval_email(self):
        subject = 'Nouvelle demande d\'inscription - Médecin'
        html_message = f"""
        <h2>Nouvelle demande d'inscription d'un médecin</h2>
        <p><strong>Nom :</strong> {self.user.get_full_name()}</p>
        <p><strong>Email :</strong> {self.user.email}</p>
        <p><strong>Email professionnel :</strong> {self.email_professionnel}</p>
        <p><strong>Spécialité :</strong> {self.specialite}</p>
        <p><strong>Numéro d'ordre :</strong> {self.numero_ordre}</p>
        <p><strong>Téléphone :</strong> {self.telephone}</p>
        <p><strong>Adresse :</strong> {self.adresse}</p>
        <p><strong>Tarif de consultation :</strong> {self.tarif}€</p>
        <p><strong>Horaires :</strong></p>
        <ul>
            <li>Lundi : {self.horaires.get('lundi', {}).get('debut')} - {self.horaires.get('lundi', {}).get('fin')}</li>
            <li>Mardi : {self.horaires.get('mardi', {}).get('debut')} - {self.horaires.get('mardi', {}).get('fin')}</li>
            <li>Mercredi : {self.horaires.get('mercredi', {}).get('debut')} - {self.horaires.get('mercredi', {}).get('fin')}</li>
            <li>Jeudi : {self.horaires.get('jeudi', {}).get('debut')} - {self.horaires.get('jeudi', {}).get('fin')}</li>
            <li>Vendredi : {self.horaires.get('vendredi', {}).get('debut')} - {self.horaires.get('vendredi', {}).get('fin')}</li>
            <li>Samedi : {self.horaires.get('samedi', {}).get('debut')} - {self.horaires.get('samedi', {}).get('fin')}</li>
        </ul>
        <p><strong>Services proposés :</strong></p>
        <ul>
            {''.join(f'<li>{service}</li>' for service in self.services)}
        </ul>
        <p>
            <a href="{settings.SITE_URL}/admin/approve/medecin/{self.id}/" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Approuver</a>
            <a href="{settings.SITE_URL}/admin/reject/medecin/{self.id}/" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Rejeter</a>
        </p>
        """
        try:
            send_mail(
                subject=subject,
                message=strip_tags(html_message),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html_message
            )
            logger.info(f"Email d'approbation envoyé à l'admin pour le médecin {self.user.email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'approbation pour le médecin {self.user.email}: {str(e)}")

    def send_approval_status_email(self, approved=True):
        try:
            logger.info(f"Début de l'envoi d'email de statut pour {self.user.email}")
            if approved:
                subject = 'Votre compte médecin a été approuvé'
                html_message = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Félicitations !</h2>
                    <p>Cher(e) {self.user.get_full_name()},</p>
                    <p>Votre compte médecin a été approuvé par l'administrateur. Vous pouvez maintenant vous connecter à votre espace professionnel.</p>
                    <p>Pour vous connecter, utilisez les identifiants suivants :</p>
                    <ul>
                        <li>Email : {self.user.email}</li>
                    </ul>
                    <p>Cliquez sur le lien ci-dessous pour accéder à votre espace :</p>
                    <p><a href="{settings.SITE_URL}/login/" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Se connecter</a></p>
                    <p>Cordialement,<br>L'équipe AlloDoc</p>
                </div>
                '''
            else:
                subject = 'Votre demande de compte médecin a été rejetée'
                html_message = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Demande rejetée</h2>
                    <p>Cher(e) {self.user.get_full_name()},</p>
                    <p>Nous regrettons de vous informer que votre demande de compte médecin a été rejetée par l'administrateur.</p>
                    <p>Si vous pensez qu'il s'agit d'une erreur, n'hésitez pas à nous contacter.</p>
                    <p>Cordialement,<br>L'équipe AlloDoc</p>
                </div>
                '''
            
            plain_message = strip_tags(html_message)
            
            logger.info(f"Préparation de l'email pour le professionnel {self.user.email}")
            logger.info(f"Configuration email: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, USER={settings.EMAIL_HOST_USER}")
            
            # Envoi de l'email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email de statut envoyé avec succès au professionnel {self.user.email}")
            
        except Exception as e:
            logger.error(f"Erreur détaillée lors de l'envoi de l'email de statut au professionnel {self.user.email}: {str(e)}")
            logger.exception("Trace complète de l'erreur:")
            raise

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10)
    telephone = models.CharField(max_length=20)
    adresse = models.CharField(max_length=200)
    groupe_sanguin = models.CharField(max_length=5, null=True, blank=True)
    antecedents_medicaux = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

class RendezVous(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('annule', 'Annulé'),
        ('termine', 'Terminé'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    motif = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    notes = models.TextField(null=True, blank=True)
    lien_visio = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RDV {self.patient} avec Dr. {self.medecin} le {self.date_heure}"

class Laboratoire(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    adresse = models.CharField(max_length=200)
    email_professionnel = models.EmailField(unique=True, null=True, blank=True)
    numero_agrement = models.CharField(max_length=50, default='')
    is_validated_by_admin = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    horaires = models.JSONField(default=dict)
    services = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom

    def send_admin_approval_email(self):
        subject = 'Nouvelle demande d\'inscription - Laboratoire'
        html_message = f"""
        <h2>Nouvelle demande d'inscription d'un laboratoire</h2>
        <p><strong>Nom :</strong> {self.nom}</p>
        <p><strong>Email :</strong> {self.user.email}</p>
        <p><strong>Email professionnel :</strong> {self.email_professionnel}</p>
        <p><strong>Numéro d'agrément :</strong> {self.numero_agrement}</p>
        <p><strong>Téléphone :</strong> {self.telephone}</p>
        <p><strong>Adresse :</strong> {self.adresse}</p>
        <p><strong>Horaires :</strong></p>
        <ul>
            <li>Lundi : {self.horaires.get('lundi', {}).get('debut')} - {self.horaires.get('lundi', {}).get('fin')}</li>
            <li>Mardi : {self.horaires.get('mardi', {}).get('debut')} - {self.horaires.get('mardi', {}).get('fin')}</li>
            <li>Mercredi : {self.horaires.get('mercredi', {}).get('debut')} - {self.horaires.get('mercredi', {}).get('fin')}</li>
            <li>Jeudi : {self.horaires.get('jeudi', {}).get('debut')} - {self.horaires.get('jeudi', {}).get('fin')}</li>
            <li>Vendredi : {self.horaires.get('vendredi', {}).get('debut')} - {self.horaires.get('vendredi', {}).get('fin')}</li>
            <li>Samedi : {self.horaires.get('samedi', {}).get('debut')} - {self.horaires.get('samedi', {}).get('fin')}</li>
        </ul>
        <p><strong>Services proposés :</strong></p>
        <ul>
            {''.join(f'<li>{service}</li>' for service in self.services)}
        </ul>
        <p>
            <a href="{settings.SITE_URL}/admin/approve/laboratoire/{self.id}/" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Approuver</a>
            <a href="{settings.SITE_URL}/admin/reject/laboratoire/{self.id}/" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Rejeter</a>
        </p>
        """
        try:
            send_mail(
                subject=subject,
                message=strip_tags(html_message),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html_message
            )
            logger.info(f"Email d'approbation envoyé à l'admin pour le laboratoire {self.user.email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'approbation pour le laboratoire {self.user.email}: {str(e)}")

    def send_approval_status_email(self, approved=True):
        try:
            if approved:
                subject = 'Votre compte laboratoire a été approuvé'
                html_message = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Félicitations !</h2>
                    <p>Cher(e) {self.nom},</p>
                    <p>Votre compte laboratoire a été approuvé par l'administrateur. Vous pouvez maintenant vous connecter à votre espace professionnel.</p>
                    <p>Pour vous connecter, utilisez les identifiants suivants :</p>
                    <ul>
                        <li>Email : {self.user.email}</li>
                    </ul>
                    <p>Cliquez sur le lien ci-dessous pour accéder à votre espace :</p>
                    <p><a href="{settings.SITE_URL}/login/" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Se connecter</a></p>
                    <p>Cordialement,<br>L'équipe AlloDoc</p>
                </div>
                '''
            else:
                subject = 'Votre demande de compte laboratoire a été rejetée'
                html_message = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Demande rejetée</h2>
                    <p>Cher(e) {self.nom},</p>
                    <p>Nous regrettons de vous informer que votre demande de compte laboratoire a été rejetée par l'administrateur.</p>
                    <p>Si vous pensez qu'il s'agit d'une erreur, n'hésitez pas à nous contacter.</p>
                    <p>Cordialement,<br>L'équipe AlloDoc</p>
                </div>
                '''
            
            plain_message = strip_tags(html_message)
            
            # Log avant l'envoi
            logger.info(f"Tentative d'envoi d'email de statut au laboratoire {self.user.email}")
            
            # Envoi de l'email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Log après l'envoi réussi
            logger.info(f"Email de statut envoyé avec succès au laboratoire {self.user.email}")
            
        except Exception as e:
            # Log en cas d'erreur
            logger.error(f"Erreur lors de l'envoi de l'email de statut au laboratoire {self.user.email}: {str(e)}")
            raise

class Pharmacien(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_officine = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    adresse = models.CharField(max_length=200)
    email_professionnel = models.EmailField(unique=True, null=True, blank=True)
    numero_ordre = models.CharField(max_length=50, default='')
    is_validated_by_admin = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    horaires = models.JSONField(default=dict)
    services = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom_officine

    def send_admin_approval_email(self):
        subject = 'Nouvelle demande d\'inscription - Pharmacien'
        html_message = f"""
        <h2>Nouvelle demande d'inscription d'un pharmacien</h2>
        <p><strong>Nom de l'officine :</strong> {self.nom_officine}</p>
        <p><strong>Email :</strong> {self.user.email}</p>
        <p><strong>Email professionnel :</strong> {self.email_professionnel}</p>
        <p><strong>Numéro d'ordre :</strong> {self.numero_ordre}</p>
        <p><strong>Téléphone :</strong> {self.telephone}</p>
        <p><strong>Adresse :</strong> {self.adresse}</p>
        <p><strong>Horaires :</strong></p>
        <ul>
            <li>Lundi : {self.horaires.get('lundi', {}).get('debut')} - {self.horaires.get('lundi', {}).get('fin')}</li>
            <li>Mardi : {self.horaires.get('mardi', {}).get('debut')} - {self.horaires.get('mardi', {}).get('fin')}</li>
            <li>Mercredi : {self.horaires.get('mercredi', {}).get('debut')} - {self.horaires.get('mercredi', {}).get('fin')}</li>
            <li>Jeudi : {self.horaires.get('jeudi', {}).get('debut')} - {self.horaires.get('jeudi', {}).get('fin')}</li>
            <li>Vendredi : {self.horaires.get('vendredi', {}).get('debut')} - {self.horaires.get('vendredi', {}).get('fin')}</li>
            <li>Samedi : {self.horaires.get('samedi', {}).get('debut')} - {self.horaires.get('samedi', {}).get('fin')}</li>
        </ul>
        <p><strong>Services proposés :</strong></p>
        <ul>
            {''.join(f'<li>{service}</li>' for service in self.services)}
        </ul>
        <p>
            <a href="{settings.SITE_URL}/admin/approve/pharmacien/{self.id}/" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Approuver</a>
            <a href="{settings.SITE_URL}/admin/reject/pharmacien/{self.id}/" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Rejeter</a>
        </p>
        """
        try:
            send_mail(
                subject=subject,
                message=strip_tags(html_message),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html_message
            )
            logger.info(f"Email d'approbation envoyé à l'admin pour le pharmacien {self.user.email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'approbation pour le pharmacien {self.user.email}: {str(e)}")

    def send_approval_status_email(self, approved=True):
        try:
            if approved:
                subject = 'Votre compte pharmacien a été approuvé'
                html_message = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Félicitations !</h2>
                    <p>Cher(e) {self.nom_officine},</p>
                    <p>Votre compte pharmacien a été approuvé par l'administrateur. Vous pouvez maintenant vous connecter à votre espace professionnel.</p>
                    <p>Pour vous connecter, utilisez les identifiants suivants :</p>
                    <ul>
                        <li>Email : {self.user.email}</li>
                    </ul>
                    <p>Cliquez sur le lien ci-dessous pour accéder à votre espace :</p>
                    <p><a href="{settings.SITE_URL}/login/" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Se connecter</a></p>
                    <p>Cordialement,<br>L'équipe AlloDoc</p>
                </div>
                '''
            else:
                subject = 'Votre demande de compte pharmacien a été rejetée'
                html_message = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Demande rejetée</h2>
                    <p>Cher(e) {self.nom_officine},</p>
                    <p>Nous regrettons de vous informer que votre demande de compte pharmacien a été rejetée par l'administrateur.</p>
                    <p>Si vous pensez qu'il s'agit d'une erreur, n'hésitez pas à nous contacter.</p>
                    <p>Cordialement,<br>L'équipe AlloDoc</p>
                </div>
                '''
            
            plain_message = strip_tags(html_message)
            
            # Log avant l'envoi
            logger.info(f"Tentative d'envoi d'email de statut à la pharmacie {self.user.email}")
            
            # Envoi de l'email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Log après l'envoi réussi
            logger.info(f"Email de statut envoyé avec succès à la pharmacie {self.user.email}")
            
        except Exception as e:
            # Log en cas d'erreur
            logger.error(f"Erreur lors de l'envoi de l'email de statut à la pharmacie {self.user.email}: {str(e)}")
            raise

class Disponibilite(models.Model):
    medecin = models.ForeignKey('Medecin', on_delete=models.CASCADE)
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    def __str__(self):
        return f"{self.medecin} - {self.date} {self.heure_debut}-{self.heure_fin}"

class Message(models.Model):
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_recus')
    contenu = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"De {self.expediteur} à {self.destinataire} : {self.contenu[:20]}..."

class Ordonnance(models.Model):
    medecin = models.ForeignKey('Medecin', on_delete=models.CASCADE)
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    medicaments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Ordonnance pour {self.patient} par {self.medecin}"

class ChatMessage(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_from_ai = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{'AI' if self.is_from_ai else 'Patient'}: {self.message[:50]}..."

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import  Q
import hashlib
import pyotp
from django.core.mail import send_mail
from django.utils.timezone import now
from django.conf import settings
from django.core.exceptions import ValidationError


#les modèles construisent les tables de la DB et
#définit la structure des données (champs, types de données, contraintes) et les comportements associés
#heriter de AbstractUser pour utiliser le modèle user de django
class CustomUser(AbstractUser):
    username = models.CharField(max_length=50, unique=True)
    email =  models.EmailField(max_length=70, unique=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.jpg')
    remote_user = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=64, blank=True, null= True)
    last_otp_hash = models.CharField(max_length=128, blank=True, null=True)
    last_otp_timestamp = models.DateTimeField(blank=True, null=True)
    enable_2fa = models.CharField(
        max_length=5,
        choices=[('none', 'None'), ('email', 'Email'), ('totp', 'TOTP')],
        default='none'
    )
    friends = models.ManyToManyField(
        'self',
        through='Friendship',
        symmetrical=False,
        related_name='related_to'
    )
    is_online = models.BooleanField(default=False)
    is_guest = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        """
        Override save to handle remote URLs and local files.
        - If `avatar` is a remote URL, save it directly as a string in the database.
        - If `avatar` is a local file, use Django's default behavior for saving local files.
        """
        if self.avatar and (self.avatar.name.startswith('http://') or self.avatar.name.startswith('https://')):
            # Save the remote URL directly in the database
            self._avatar = self.avatar.name
            self.avatar.storage = None  # Prevent Django from treating it as a local file
        else:
            # Use the default behavior for local files
            self._avatar = None
        super().save(*args, **kwargs)

    def hash_otp(self, otp):
        """Hash the OTP for secure storage."""
        return hashlib.sha256(otp.encode('utf-8')).hexdigest()

    def send_otp_email(self):
        """Send OTP to the user's email."""
        totp = pyotp.TOTP(self.otp_secret)
        otp_code = totp.now()
        try:
            send_mail(
                subject="Your Login OTP Code",
                message=f"Your OTP code is {otp_code}. It expires in 60 seconds. If it has expired please redo the login.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[self.email],
            )
        except Exception as e:
            print(f"Error sending email: {str(e)}")  # To debug email sending errors
            raise e
        return otp_code

    def validate_otp(self, otp):
        """Validate the OTP and check for replay attacks."""
        totp = pyotp.TOTP(self.otp_secret)

        # Ensure OTP is valid and within the window
        if not totp.verify(otp, valid_window=2):
            #raise ValidationError("Invalid or expired OTP.")
            return False

        # Check for replay attacks (same OTP used multiple times)
        otp_hash = self.hash_otp(otp)
        if self.last_otp_hash == otp_hash:
            #raise ValidationError("This OTP has already been used.")
            return False

        # Update OTP tracking data
        self.last_otp_hash = otp_hash
        self.last_otp_timestamp = now()
        self.save(update_fields=['last_otp_hash', 'last_otp_timestamp'])

        return True  # OTP is valid
    
    def set_password(self, raw_password):
        super().set_password(raw_password)


User = get_user_model()

class Friendship(models.Model):
    from_user = models.ForeignKey(
        User, 
        related_name='friendships_sent', 
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User, 
        related_name='friendships_received', 
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    has_rights = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friendship')
        ]

    def __str__(self):
        return f"{self.from_user.username} is friends with {self.to_user.username}"

    #Valide que from_user et to_user ne sont pas la même personne
    def clean(self):
        if self.from_user == self.to_user:
            raise ValidationError("You cannot add yourself as a friend.")
        
        if Friendship.objects.filter(
            Q(from_user=self.from_user, to_user=self.to_user, is_blocked=True) |
            Q(from_user=self.to_user, to_user=self.from_user, is_blocked=True)
        ).exists()and not self.is_blocked:
            raise ValidationError("You cannot interact with a blocked user.")
#app le clean er enregistre
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
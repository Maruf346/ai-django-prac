from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid


class AuthProvider(models.TextChoices):
    SELF = 'self', 'Self'
    GOOGLE = 'google', 'Google'
    GITHUB = 'github', 'Github'
    FACEBOOK = 'facebook', 'Facebook'
    APPLE = 'apple', 'Apple'
    LINKEDIN = 'linkedin', 'LinkedIn'
    

class UserManager(BaseUserManager):
    use_in_migrations = True
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("You can't create user without an email address")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if not password:
            raise ValueError("Please set a password")
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is False:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is False:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)
        

class User(AbstractUser):
    
    # Older approach for choice fields
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Rather not specify'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\+8801[3-9]\d{8}$',
        message="Phone number must be entered in Bangladeshi format: '+8801XXXXXXXXX'"
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(validators=[phone_regex], max_length=14, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128)
    profile_picture = models.ImageField(upload_to='dps/', null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.IntegerField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    total_spent = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # provider details
    provider = models.CharField(
        max_length=20,
        choices=AuthProvider.choices,
        default=AuthProvider.SELF
    )
    provider_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return f"Name: {self.first_name if self.first_name else 'John Doe'} | Email: {self.email}"
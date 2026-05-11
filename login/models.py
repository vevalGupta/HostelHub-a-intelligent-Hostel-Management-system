from django import forms
from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Email is required')
        user = self.model(username=username, email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('noise', 'Noise'),
        ('internet', 'Internet'),
        ('security', 'Security'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=False)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    attachment = models.ImageField(upload_to='complaint_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.name}"
    
class Fee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}"
    
    
class Floor(models.Model):
    number = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)   # "First Floor", "Second Floor"
    

    class Meta:
        ordering = ['number']

    def __str__(self):
        return self.name

class Room(models.Model):
    ROOM_TYPES = [
        ('single',  'Single'),
        ('double',  'Double Sharing'),
        ('triple',  'Triple Sharing'),
    ]
    POSITION_CHOICES = [
        ('top',    'Top Row'),
        ('bottom', 'Bottom Row'),
    ]

    number               = models.CharField(max_length=10, unique=True)   # e.g. "A-101"
    floor                = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_type            = models.CharField(max_length=10, choices=ROOM_TYPES, default='double')
    capacity             = models.PositiveIntegerField(default=2)
    price_per_semester   = models.DecimalField(max_digits=10, decimal_places=2, default=45000)
    attached_washroom    = models.BooleanField(default=False)
    is_female_block      = models.BooleanField(default=False)
    position             = models.CharField(max_length=6, choices=POSITION_CHOICES, default='top',
                                            help_text="Visual row in the floor map")
    # Amenities stored as comma-separated slugs: wifi,study_table,wardrobe,ac
    amenities            = models.CharField(max_length=200, blank=True,
                                            help_text="Comma-separated: wifi, study_table, wardrobe, ac")

    class Meta:
        ordering = ['number']

    def __str__(self):
        return self.number

    @property
    def current_occupancy(self):
        return self.allocations.count()

    def get_status(self):
        if self.is_female_block:
            return 'female'
        if self.current_occupancy >= self.capacity:
            return 'occupied'
        return 'available'

    def amenities_list(self):
        if not self.amenities:
            return []
        return [a.strip() for a in self.amenities.split(',') if a.strip()]

    
class Allocation(models.Model):
    student    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='allocation')
    room       = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='allocations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'room')

    def __str__(self):
        return f"{self.student.username} → {self.room.number}"
    
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, blank=True)
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    student_id = models.CharField(max_length=20, unique=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    
    # "Role", "Member Since", and "Account Status" can be derived from the built-in User model:
    # Role -> user.groups or custom logic
    # Member Since -> user.date_joined
    # Last Login -> user.last_login
    # Account Status -> user.is_active

    def __str__(self):
        return self.user.username

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255) # e.g., "Logged in", "Fee payment completed"
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp'] # Newest first

    def __str__(self):
        return f"{self.user.username} - {self.action}"
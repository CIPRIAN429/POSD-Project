from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Course, Material, User
from .services import validate_prerequisites


class StyledFormMixin:
    def style_fields(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class CourseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'instructor', 'capacity', 'status', 'prerequisites']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.instance.organization_id = actor.organization_id
        self.fields['instructor'].queryset = User.objects.filter(
            organization=actor.organization, role=User.Role.INSTRUCTOR, is_active=True)
        self.fields['prerequisites'].queryset = Course.objects.filter(organization=actor.organization).exclude(pk=self.instance.pk)
        self.fields['prerequisites'].help_text = 'Hold Ctrl or Command to select more than one course.'
        # Archive through the explicit action, which also updates the waitlist.
        self.fields['status'].choices = [(Course.Status.DRAFT, 'Draft'), (Course.Status.PUBLISHED, 'Published')]
        if actor.role == User.Role.INSTRUCTOR:
            self.fields.pop('instructor')
            self.instance.instructor = actor
        self.style_fields()

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk and self.instance.status == Course.Status.ARCHIVED:
            raise ValidationError('Archived courses are read-only.')
        prerequisites = list(cleaned.get('prerequisites', []))
        validate_prerequisites(self.instance, prerequisites)
        if self.instance.pk:
            active = self.instance.enrollments.filter(status='ENROLLED').count()
            if cleaned.get('capacity', 0) < active:
                self.add_error('capacity', 'Capacity cannot be lower than the active enrollment count.')
            if cleaned.get('status') == 'DRAFT' and self.instance.enrollments.exclude(status='CANCELLED').exists():
                self.add_error('status', 'Courses with participants can be published or archived, not returned to draft.')
        return cleaned


class MaterialForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Material
        fields = ['title', 'kind', 'body', 'pdf_file', 'position']
        widgets = {'body': forms.Textarea(attrs={'rows': 12})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pdf_file'].help_text = 'PDF files only, up to 10 MB. Downloads require course access.'
        self.style_fields()

    def clean_pdf_file(self):
        upload = self.cleaned_data.get('pdf_file')
        if upload and hasattr(upload, 'content_type'):
            if upload.size > 10 * 1024 * 1024 or not upload.name.lower().endswith('.pdf'):
                raise ValidationError('Upload a PDF file no larger than 10 MB.')
            signature = upload.read(5)
            upload.seek(0)
            if signature != b'%PDF-':
                raise ValidationError('The uploaded file is not a PDF.')
        return upload

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('kind') == 'TEXT' and not cleaned.get('body', '').strip():
            self.add_error('body', 'A text lesson needs content.')
        if cleaned.get('kind') == 'PDF' and not cleaned.get('pdf_file'):
            self.add_error('pdf_file', 'A PDF handout needs a file.')
        return cleaned


class OrganizationUserForm(StyledFormMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False,
                               help_text='Set an initial password, or leave blank when editing to keep the current password.')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'is_active', 'password']

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.instance.organization_id = actor.organization_id
        self.fields['password'].required = not bool(self.instance.pk)
        self.style_fields()

    def clean_password(self):
        value = self.cleaned_data.get('password')
        if value:
            validate_password(value, self.instance)
        return value

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk == self.actor.pk:
            if cleaned.get('role') != 'ADMIN' or not cleaned.get('is_active'):
                raise ValidationError('You cannot deactivate or remove your own administrator role.')
        if self.instance.pk:
            if cleaned.get('role') != 'INSTRUCTOR' and self.instance.teaching_courses.exists():
                self.add_error('role', 'Reassign this instructor\'s courses before changing the role.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.organization_id = self.actor.organization_id
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        else:
            # ModelForm's declared password field must not overwrite the existing hash.
            user.password = User.objects.get(pk=user.pk).password
        if commit:
            user.save()
        return user

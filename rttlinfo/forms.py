from django import forms
from django.core.exceptions import ValidationError
from .dataclasses import CourseConfiguration, GitpullerTarget


class GitpullerTargetForm(forms.Form):
    """
    Form for individual gitpuller targets.
    """
    gitpuller_uri = forms.URLField(
        label='Git Repository URI',
        help_text='URL of the git repository to clone',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/username/repository.git'
        })
    )

    gitpuller_tag = forms.CharField(
        label='Git Branch or Tag',
        help_text='Branch or tag to checkout (e.g., main, master, v1.0)',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'main'
        })
    )

    gitpuller_sync_dir = forms.CharField(
        label='Target Directory',
        help_text='Directory where the repository will be synced',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'course-materials'
        })
    )


class CourseConfigurationForm(forms.Form):
    """
    Form for creating/updating course configurations using dataclass.
    """

    # Resource requests
    cpu_request = forms.IntegerField(
        label='CPU Request (cores)',
        help_text='Number of CPU cores to request (e.g., 1, 2)',
        required=False,
        min_value=1,
        max_value=8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1'
        })
    )

    memory_request = forms.IntegerField(
        label='Memory Request (GB)',
        help_text='Amount of memory to request in gigabytes',
        required=False,
        min_value=1,
        max_value=32,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2'
        })
    )

    storage_request = forms.IntegerField(
        label='Storage Request (GB)',
        help_text='Amount of storage to request in gigabytes',
        required=False,
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10'
        })
    )

    # Container image
    image_uri = forms.CharField(
        label='Container Image URI',
        help_text='Docker image repository URI (e.g., jupyter/scipy-notebook)',
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'jupyter/scipy-notebook'
        })
    )

    image_tag = forms.CharField(
        label='Image Tag',
        help_text='Docker image tag (e.g., latest, python-3.9)',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'latest'
        })
    )

    # Features
    features_request = forms.CharField(
        label='Requested Features',
        help_text='Comma-separated list of features (e.g., '
        'nfs, binderhub, oidcauth)',
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nfs, oidcauth'
        })
    )

    # Gitpuller targets (simplified - single target for now)
    gitpuller_uri = forms.URLField(
        label='Git Repository URI (Optional)',
        help_text='URL of a git repository to automatically '
        'clone for students',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/username/course-materials.git'
        })
    )

    gitpuller_tag = forms.CharField(
        label='Git Branch/Tag (Optional)',
        help_text='Branch or tag to checkout',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'main'
        })
    )

    gitpuller_sync_dir = forms.CharField(
        label='Sync Directory (Optional)',
        help_text='Directory where the repository will be synced',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'course-materials'
        })
    )

    # Comments
    configuration_comments = forms.CharField(
        label='Additional Comments',
        help_text='Any additional information or special requirements',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please describe any special requirements or'
            'preferences...'
        })
    )

    def clean(self):
        """
        Validate the form data and ensure gitpuller fields are consistent.
        """
        cleaned_data = super().clean()

        # Validate gitpuller fields - if one is provided, others should be too
        gitpuller_uri = cleaned_data.get('gitpuller_uri')
        gitpuller_tag = cleaned_data.get('gitpuller_tag')
        gitpuller_sync_dir = cleaned_data.get('gitpuller_sync_dir')

        gitpuller_fields = [gitpuller_uri, gitpuller_tag, gitpuller_sync_dir]
        provided_fields = [f for f in gitpuller_fields if f]

        if provided_fields and len(provided_fields) != len(gitpuller_fields):
            raise ValidationError(
                "If you provide git repository information, please fill in"
                "all three fields: URI, Branch/Tag, and Sync Directory."
            )

        return cleaned_data

    def clean_features_request(self):
        """
        Validate and clean the features request field.
        """
        features = self.cleaned_data.get('features_request', '')
        if features:
            # Clean up the comma-separated values
            feature_list = [f.strip().lower() for
                            f in features.split(',') if f.strip()]

            # Validate known features (optional - you can expand this list)
            valid_features = {'nfs', 'binderhub', 'nocanvas', 'oidcauth'}
            invalid_features = [f for f in feature_list if
                                f not in valid_features]

            if invalid_features:
                raise ValidationError(
                    f"Unknown features: {', '.join(invalid_features)}. "
                    f"Valid features are: {', '.join(sorted(valid_features))}"
                )

            return ', '.join(feature_list)
        return features

    def to_dataclass(self) -> CourseConfiguration:
        """
        Convert form data to CourseConfiguration dataclass.
        """
        if not self.is_valid():
            raise ValueError("Form is not valid")

        data = self.cleaned_data

        # Create gitpuller targets list
        gitpuller_targets = []
        if data.get('gitpuller_uri'):
            gitpuller_targets.append(GitpullerTarget(
                gitpuller_uri=data['gitpuller_uri'],
                gitpuller_tag=data['gitpuller_tag'] or 'main',
                gitpuller_sync_dir=data['gitpuller_sync_dir'] or
                'course-materials'
            ))

        return CourseConfiguration(
            # New configurations start as not applied
            configuration_applied=False,
            cpu_request=data.get('cpu_request'),
            memory_request=data.get('memory_request'),
            storage_request=data.get('storage_request'),
            image_uri=data.get('image_uri', ''),
            image_tag=data.get('image_tag', ''),
            features_request=data.get('features_request', ''),
            gitpuller_targets=gitpuller_targets,
            configuration_comments=data.get('configuration_comments', '')
        )

    def from_dataclass(self, config: CourseConfiguration):
        """
        Populate form fields from CourseConfiguration dataclass.
        """
        self.initial = {
            'cpu_request': config.cpu_request,
            'memory_request': config.memory_request,
            'storage_request': config.storage_request,
            'image_uri': config.image_uri,
            'image_tag': config.image_tag,
            'features_request': config.features_request,
            'configuration_comments': config.configuration_comments,
        }

        # Handle first gitpuller target if exists
        if config.gitpuller_targets:
            first_target = config.gitpuller_targets[0]
            self.initial.update({
                'gitpuller_uri': first_target.gitpuller_uri,
                'gitpuller_tag': first_target.gitpuller_tag,
                'gitpuller_sync_dir': first_target.gitpuller_sync_dir,
            })


class CourseStatusForm(forms.Form):
    """
    Form for creating course status updates.
    """

    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('provisioning', 'Provisioning'),
        ('ready', 'Ready'),
        ('error', 'Error'),
        ('deleted', 'Deleted'),
    ]

    sis_course_id = forms.CharField(
        label='Course SIS ID',
        help_text='Student Information System course identifier',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True  # Usually pre-filled from context
        })
    )

    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        initial='requested',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    auto_create = forms.BooleanField(
        label='Auto-create course if not exists',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    hub_deployed = forms.BooleanField(
        label='Hub is deployed',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    message = forms.CharField(
        label='Status Message',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional status message...'
        })
    )

    # Course information (for auto-creation)
    name = forms.CharField(
        label='Course Name',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Introduction to Data Science'
        })
    )

    course_year = forms.IntegerField(
        label='Course Year',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2025'
        })
    )

    course_quarter = forms.CharField(
        label='Course Quarter',
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'spring'
        })
    )

    hub_url = forms.URLField(
        label='Hub URL',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://course.jupyter.uw.edu'
        })
    )


class HubRequestForm(forms.Form):
    """
    Combined form for requesting a new JupyterHub.
    """

    # Course information
    course_name = forms.CharField(
        label='Course Name',
        help_text='Full name of your course',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Introduction to Data Science'
        })
    )

    instructor_name = forms.CharField(
        label='Instructor Name',
        help_text='Primary instructor for this course',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name'
        })
    )

    instructor_email = forms.EmailField(
        label='Instructor Email',
        help_text='Contact email for hub-related communications',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'instructor@uw.edu'
        })
    )

    expected_students = forms.IntegerField(
        label='Expected Number of Students',
        help_text='Approximate number of students who will use the hub',
        min_value=1,
        max_value=500,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '25'
        })
    )

    # Include configuration fields
    cpu_request = forms.IntegerField(
        label='CPU Request (cores)',
        help_text='Number of CPU cores per student (1-2 recommended)',
        required=False,
        min_value=1,
        max_value=4,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )

    memory_request = forms.IntegerField(
        label='Memory Request (GB)',
        help_text='Amount of memory per student in GB (2-8 recommended)',
        required=False,
        min_value=1,
        max_value=16,
        initial=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )

    storage_request = forms.IntegerField(
        label='Storage Request (GB)',
        help_text='Amount of storage per student in GB',
        required=False,
        min_value=1,
        max_value=50,
        initial=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )

    special_requirements = forms.CharField(
        label='Special Requirements',
        help_text='Any special software, packages, or configuration needs',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe any special requirements, '
            'software packages, or configurations needed for your course...'
        })
    )

    def clean_instructor_email(self):
        """
        Validate that the email is a UW email (optional).
        """
        email = self.cleaned_data.get('instructor_email')
        if email and not email.endswith('@uw.edu'):
            # This is optional - you might want to allow other email domains
            pass
        return email

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
    cpu_request = forms.ChoiceField(
        label='CPU Request (cores)',
        help_text='Number of CPU cores requested for each user environment',
        required=False,
        choices=[('1', '1 core'), ('2', '2 cores'), ('4', '4 cores')],
        initial='1',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    memory_request = forms.ChoiceField(
        label='Memory Request (GB)',
        help_text=(
            'Amount of memory requested in gigabytes for each user environment'
        ),
        required=False,
        choices=[('2', '2 GB'), ('4', '4 GB')],
        initial='2',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    storage_request = forms.ChoiceField(
        label='Storage Request (GB)',
        help_text=('Amount of storage requested in gigabytes for each user\'s '
                   'home directory'),
        required=False,
        choices=[('5', '5 GB'), ('10', '10 GB')],
        initial='5',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    # Container image - changed to radio buttons
    container_image = forms.ChoiceField(
        label='Container Image',
        help_text='Select the image to be used for your course',
        required=False,
        choices=[
            ('scipy', 'SciPy - Scientific computing with Python [<a href='
             '"https://github.com/uw-it-aca/rttl-notebooks/tree/main/scipy" '
             'target="_blank">Image details</a>]'),
            ('datascience', 'Datascience - Data analysis and visualization [<a href='
             '"https://github.com/uw-it-aca/rttl-notebooks/tree/main/datascience" '
             'target="_blank">Image details</a>]'),
            ('tensorflow', 'TensorFlow - Machine learning and deep learning [<a href='
             '"https://github.com/uw-it-aca/rttl-notebooks/tree/main/tensorflow" '
             'target="_blank">Image details</a>]'),
            ('r', 'R - Statistical computing and graphics [<a href='
             '"https://github.com/uw-it-aca/rttl-notebooks/tree/main/r" '
             'target="_blank">Image details</a>]'),
            ('rstudio', 'RStudio Server (Open Source Edition) [<a href='
             '"https://github.com/uw-it-aca/rttl-notebooks/tree/main/rstudio" '
             'target="_blank">Image details</a>]'),
            ('rstudio-ai', 'RStudio Server with AI integrations enabled [<a href='
             '"https://github.com/uw-it-aca/rttl-notebooks/tree/main/ai" '
             'target="_blank">Image details</a>]'),
            ('custom', 'Custom image (instructor supported)'),
        ],
        initial='scipy',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    # Custom image fields
    custom_image_url = forms.CharField(
        label='Image URL',
        help_text='Docker image URL (e.g., jupyter/minimal-notebook)',
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'jupyter/minimal-notebook'
        })
    )

    custom_image_tag = forms.CharField(
        label='Image Tag',
        help_text='Image tag to use (e.g., latest, v1.0)',
        required=False,
        empty_value='latest',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'latest'
        })
    )

    # Features (NFS is the only one for now)
    feature_nfs = forms.BooleanField(
        label='NFS',
        help_text='Network File System for shared storage in the Hub',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    # Let in as a stub for future use
    feature_binderhub = forms.BooleanField(
        label='BinderHub',
        help_text='Enable BinderHub integration',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    # Gitpuller targets (simplified - single target for now)
    gitpuller_uri = forms.URLField(
        label='Git Repository URI',
        help_text='URL of a git repository to automatically '
        'sync in each student\'s home directory. Please review the '
        '<a href="https://uwconnect.uw.edu/it?id=kb_article_view&sysparm_article=KB0034611" target="_blank">best practices</a> for using gitpuller.',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/username/course-materials.git'
        })
    )

    gitpuller_tag = forms.CharField(
        label='Git Branch',
        help_text='Branch to checkout',
        empty_value='main',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'main'
        })
    )

    gitpuller_sync_dir = forms.CharField(
        label='Sync Directory',
        help_text='Directory where the repository will be synced in each user\'s home directory',
        empty_value='COURSE_MATERIALS',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'COURSE_MATERIALS'  # Default sync directory
        })
    )

    additional_admins = forms.CharField(
        label='Additional Hub Admins',
        help_text='Comma-separated list of UW NetIDs to add as additional Hub admins',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 1,
            'placeholder': 'Enter UW NetIDs...'
        })
    )

    # Comments
    configuration_comments = forms.CharField(
        label='Comments',
        help_text='Any additional information or special requirements',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please describe any special requirements or'
            ' preferences...'
        })
    )

    def clean(self):
        """
        Validate the form data and ensure gitpuller fields are consistent.
        """
        cleaned_data = super().clean()

        # Validate custom image fields if custom is selected
        container_image = cleaned_data.get('container_image')
        custom_image_url = cleaned_data.get('custom_image_url')
        custom_image_tag = cleaned_data.get('custom_image_tag')

        if container_image == 'custom':
            if not custom_image_url:
                raise ValidationError("Image URL is required when using a custom image.")
            if not custom_image_tag:
                raise ValidationError("Image Tag is required when using a custom image.")

        # Validate gitpuller fields
        gitpuller_uri = cleaned_data.get('gitpuller_uri')
        gitpuller_tag = cleaned_data.get('gitpuller_tag')
        gitpuller_sync_dir = cleaned_data.get('gitpuller_sync_dir')

        if gitpuller_uri:
            # If URI is provided, ensure we have tag and sync_dir
            # Use defaults if they're empty
            # Both have empty values set if the user did not provide them
            if not gitpuller_tag:
                cleaned_data['gitpuller_tag']
            if not gitpuller_sync_dir:
                cleaned_data['gitpuller_sync_dir']

        return cleaned_data

    def get_features_list(self):
        """
        Convert checkbox selections to features list.
        """
        features = []
        if self.cleaned_data.get('feature_nfs'):
            features.append('nfs')
        if self.cleaned_data.get('feature_binderhub'):
            features.append('binderhub')
        return features

    def get_hub_admins_list(self):
        """
        Convert additional_admins field to a list of admin NetIDs.
        """
        additional_admins = self.cleaned_data.get('additional_admins', '')
        if not additional_admins:
            return None

        # Split by comma and clean up whitespace also ensure no email addresses
        admins = [admin.strip().split('@')[0] for admin in
                  additional_admins.split(',') if admin.strip()]
        return admins if admins else None

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
                gitpuller_tag=data['gitpuller_tag'],
                gitpuller_sync_dir=data['gitpuller_sync_dir']
            ))

        # Handle container image - either predefined or custom
        container_choice = data.get('container_image')
        
        if container_choice == 'custom':
            image_uri = data.get('custom_image_url')
            image_tag = data.get('custom_image_tag')
        else:
            # Map container image choices to actual image URIs
            image_mapping = {
                'scipy': ('us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-scipy-notebook', '2.7.1'),
                'datascience': ('us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-datascience-notebook', '2.7.1'),
                'tensorflow': ('us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-tensorflow-notebook', '2.7.1'),
                'r': ('us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-r-notebook', '2.7.1'),
                'rstudio': ('us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-rstudio-notebook', '2.7.1'),
                'rstudio-ai': ('us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-ai-notebook', '2.7.0'),
            }
            image_uri, image_tag = image_mapping.get(container_choice, image_mapping['scipy'])

        # Get features from checkboxes
        features_list = self.get_features_list()
        features_request = ', '.join(features_list) if features_list else ''

        return CourseConfiguration(
            configuration_applied=False,
            cpu_request=int(data.get('cpu_request', '1')),
            memory_request=int(data.get('memory_request', '2')),
            storage_request=int(data.get('storage_request', '5')),
            image_uri=image_uri,
            image_tag=image_tag,
            features_request=features_request,
            gitpuller_targets=gitpuller_targets,
            configuration_comments=data.get('configuration_comments', '')
        )

    def from_dataclass(self, config: CourseConfiguration):
        """
        Populate form fields from CourseConfiguration dataclass.
        """
        # Map image URIs back to container choices
        image_reverse_mapping = {
            'us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-scipy-notebook': 'scipy',
            'us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-datascience-notebook': 'datascience',
            'us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-tensorflow-notebook': 'tensorflow',
            'us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-r-notebook': 'r',
            'us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-rstudio-notebook': 'rstudio',
            'us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/jupyter-ai-notebook': 'rstudio-ai',
        }

        container_choice = image_reverse_mapping.get(config.image_uri, 'custom')

        # Parse features string to set checkboxes
        features_list = [f.strip().lower() for f in config.features_request.split(',') if f.strip()] if config.features_request else []

        self.initial = {
            'cpu_request': str(config.cpu_request),
            'memory_request': str(config.memory_request),
            'storage_request': str(config.storage_request),
            'container_image': container_choice,
            'feature_nfs': 'nfs' in features_list,
            'feature_binderhub': 'binderhub' in features_list,
            'configuration_comments': config.configuration_comments,
        }

        # If it's a custom image, populate custom fields
        if container_choice == 'custom':
            self.initial.update({
                'custom_image_url': config.image_uri,
                'custom_image_tag': config.image_tag,
            })

        # Handle first gitpuller target if exists
        if config.gitpuller_targets:
            first_target = config.gitpuller_targets[0]
            self.initial.update({
                'gitpuller_uri': first_target.gitpuller_uri,
                'gitpuller_tag': first_target.gitpuller_tag,
                'gitpuller_sync_dir': first_target.gitpuller_sync_dir,
            })

    def set_hub_admins(self, hub_admins_list):
        """
        Set the hub admins field from a list of admin NetIDs.
        """
        if hub_admins_list:
            self.initial['additional_admins'] = ', '.join(hub_admins_list)
        else:
            self.initial['additional_admins'] = ''


class CourseStatusForm(forms.Form):
    """
    Form for creating course status updates.
    """

    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('blocked', 'Blocked'),
        ('pending', 'Pending'),
        ('deployed', 'Deployed'),
        ('archived', 'Archived'),
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
        label='Auto-create course if it does not exist',
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
            'placeholder': 'https://jupyter.rttl.uw.edu/course_sis_id'
        })
    )

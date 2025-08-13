# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError


@dataclass
class AdminImage:
    """
    Data class representing a Docker image available for JupyterHub.
    Maps to the AdminImage schema from the RTTL API.
    """
    id: int
    repo: str
    tag: str
    name: str
    description: str = ""

    def __str__(self):
        return f"{self.name} ({self.repo}:{self.tag})"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'AdminImage':
        """
        Create AdminImage instance from API response data.
        """
        return cls(
            id=data['id'],
            repo=data['repo'],
            tag=data['tag'],
            name=data['name'],
            description=data.get('description', '')
        )


@dataclass
class AdminCourseExtraEnv:
    """
    Data class representing additional environment variables for a JupyterHub.
    Maps to the AdminCourseExtraEnv schema from the API.
    """
    id: int
    key: str
    value: str

    def __str__(self):
        return f"{self.key}={self.value}"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'AdminCourseExtraEnv':
        """
        Create AdminCourseExtraEnv instance from API response data.
        """
        return cls(
            id=data['id'],
            key=data['key'],
            value=data['value']
        )


@dataclass
class AdminCourseGitPullerTarget:
    """
    Data class representing git-puller targets for a JupyterHub.
    Maps to the AdminCourseGitPullerTarget schema from the API.
    """
    id: int
    key: str
    repo: str
    branch: str
    target_dir: str

    def __str__(self):
        return f"{self.key}: {self.repo}@{self.branch} -> {self.target_dir}"

    @classmethod
    def from_api_data(
            cls, data: Dict[str, Any]) -> 'AdminCourseGitPullerTarget':
        """
        Create AdminCourseGitPullerTarget instance from API response data.
        """
        return cls(
            id=data['id'],
            key=data['key'],
            repo=data['repo'],
            branch=data['branch'],
            target_dir=data['target_dir']
        )


@dataclass
class AdminCourseSettings:
    """
    Data class representing JupyterHub settings for an admin course.
    Maps to the AdminCourseSettings schema from the API.
    """
    id: int
    course: int  # Foreign key reference to AdminCourse ID
    image: Optional[AdminImage] = None
    storage_capacity: str = "1Gi"
    cpu_request: str = "0.5"
    cpu_limit: str = "1"
    memory_request: str = "512Mi"
    memory_limit: str = "1Gi"
    lab_ui: bool = True
    placeholder_count: int = 0
    cull_time: int = 3600
    spawner: str = "kubespawner"
    image_puller_enabled: bool = True
    image_tag: Optional[str] = None
    feature_nfs: bool = False
    feature_binderhub: bool = False
    feature_nocanvas: bool = False
    feature_oidcauth: bool = False
    extra_envs: List[AdminCourseExtraEnv] = field(default_factory=list)
    git_puller_targets: List[AdminCourseGitPullerTarget] = \
        field(default_factory=list)

    def __str__(self):
        return f"Settings for course {self.course}"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'AdminCourseSettings':
        """
        Create AdminCourseSettings instance from API response data.
        """
        # Handle nested image object
        image = None
        if data.get('image'):
            image = AdminImage.from_api_data(data['image'])

        # Handle nested extra_envs
        extra_envs = []
        if 'extra_envs' in data:
            extra_envs = [AdminCourseExtraEnv.from_api_data(env) for env in
                          data['extra_envs']]

        # Handle nested git_puller_targets
        git_puller_targets = []
        if 'git_puller_targets' in data:
            git_puller_targets = [
                AdminCourseGitPullerTarget.from_api_data(target) for target in
                data['git_puller_targets']
            ]

        return cls(
            id=data['id'],
            course=data['course'],
            image=image,
            storage_capacity=data.get('storage_capacity', '1Gi'),
            cpu_request=data.get('cpu_request', '0.5'),
            cpu_limit=data.get('cpu_limit', '1'),
            memory_request=data.get('memory_request', '512Mi'),
            memory_limit=data.get('memory_limit', '1Gi'),
            lab_ui=data.get('lab_ui', True),
            placeholder_count=data.get('placeholder_count', 0),
            cull_time=data.get('cull_time', 3600),
            spawner=data.get('spawner', 'kubespawner'),
            image_puller_enabled=data.get('image_puller_enabled', True),
            image_tag=data.get('image_tag'),
            feature_nfs=data.get('feature_nfs', False),
            feature_binderhub=data.get('feature_binderhub', False),
            feature_nocanvas=data.get('feature_nocanvas', False),
            feature_oidcauth=data.get('feature_oidcauth', False),
            extra_envs=extra_envs,
            git_puller_targets=git_puller_targets
        )


@dataclass
class AdminCourseList:
    """
    Data class representing an admin course in list view.
    Maps to the AdminCourseList schema from the API.
    """
    id: int
    key: str
    name: str
    sis_course_id: str
    hub_status: str
    hub_url: str
    last_changed: datetime

    def __str__(self):
        return f"{self.name} ({self.sis_course_id})"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'AdminCourseList':
        """
        Create AdminCourseList instance from API response data.
        """
        return cls(
            id=data['id'],
            key=data['key'],
            name=data['name'],
            sis_course_id=data['sis_course_id'],
            hub_status=data['hub_status'],
            hub_url=data['hub_url'],
            last_changed=parse_api_datetime(data['last_changed'])
        )


@dataclass
class AdminCourseDetail:
    """
    Data class representing an admin course in detail view.
    Maps to the AdminCourseDetail schema from the API.
    """
    id: int
    key: str
    name: str
    settings: AdminCourseSettings
    code: str
    sis_course_id: str
    contact_name: str
    contact_email: str
    hub_url: str
    hub_status: str
    hub_token: str
    last_changed: datetime
    welcome_email_sent: bool

    def __post_init__(self):
        """
        Validate email if provided.
        """
        if self.contact_email:
            validator = EmailValidator()
            try:
                validator(self.contact_email)
            except ValidationError as e:
                raise ValueError(f"Invalid contact email: {e}")

    def __str__(self):
        return f"{self.name} ({self.sis_course_id})"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'AdminCourseDetail':
        """
        Create AdminCourseDetail instance from API response data.
        """
        settings = AdminCourseSettings.from_api_data(data['settings'])

        return cls(
            id=data['id'],
            key=data['key'],
            name=data['name'],
            settings=settings,
            code=data['code'],
            sis_course_id=data['sis_course_id'],
            contact_name=data['contact_name'],
            contact_email=data['contact_email'],
            hub_url=data['hub_url'],
            hub_status=data['hub_status'],
            hub_token=data['hub_token'],
            last_changed=parse_api_datetime(data['last_changed']),
            welcome_email_sent=data['welcome_email_sent']
        )


@dataclass
class GitpullerTarget:
    """
    Data class representing gitpuller targets within a configuration.
    Maps to the GitpullerTarget schema from the API.
    """
    gitpuller_uri: str
    gitpuller_tag: str
    gitpuller_sync_dir: str

    def __str__(self):
        return f"{self.gitpuller_uri}@{self.gitpuller_tag} -> \
        {self.gitpuller_sync_dir}"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'GitpullerTarget':
        """
        Create GitpullerTarget instance from API response data.
        """
        return cls(
            gitpuller_uri=data['gitpuller_uri'],
            gitpuller_tag=data['gitpuller_tag'],
            gitpuller_sync_dir=data['gitpuller_sync_dir']
        )

    def to_api_data(self) -> Dict[str, Any]:
        """
        Convert to API format.
        """
        return {
            'gitpuller_uri': self.gitpuller_uri,
            'gitpuller_tag': self.gitpuller_tag,
            'gitpuller_sync_dir': self.gitpuller_sync_dir
        }


@dataclass
class CourseConfiguration:
    """
    Data class representing a course configuration.
    Maps to the CourseConfiguration schema from the API.
    """
    configuration_applied: bool = False
    cpu_request: Optional[int] = None
    memory_request: Optional[int] = None
    storage_request: Optional[int] = None
    image_uri: str = ""
    image_tag: str = ""
    features_request: str = ""
    gitpuller_targets: List[GitpullerTarget] = field(default_factory=list)
    configuration_comments: str = ""
    create_timestamp: Optional[datetime] = None

    def get_features_list(self) -> List[str]:
        """
        Return features as a list.
        """
        if not self.features_request:
            return []
        return [feature.strip() for feature in self.features_request.split(',')
                if feature.strip()]

    def set_features_list(self, features_list: List[str]) -> None:
        """
        Set features from a list.
        """
        self.features_request = ', '.join(features_list)

    def __str__(self):
        return f"Configuration - Applied: {self.configuration_applied}"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'CourseConfiguration':
        """
        Create CourseConfiguration instance from API response data.
        """
        gitpuller_targets = []
        if 'gitpuller_targets' in data:
            gitpuller_targets = [GitpullerTarget.from_api_data(target) for
                                 target in data['gitpuller_targets']]

        return cls(
            configuration_applied=data.get('configuration_applied', False),
            cpu_request=data.get('cpu_request'),
            memory_request=data.get('memory_request'),
            storage_request=data.get('storage_request'),
            image_uri=data.get('image_uri', ''),
            image_tag=data.get('image_tag', ''),
            features_request=data.get('features_request', ''),
            gitpuller_targets=gitpuller_targets,
            configuration_comments=data.get('configuration_comments', ''),
            create_timestamp=parse_api_datetime(data.get('create_timestamp'))
        )

    def to_api_data(self) -> Dict[str, Any]:
        """
        Convert to API format.
        """
        return {
            'configuration_applied': self.configuration_applied,
            'cpu_request': self.cpu_request,
            'memory_request': self.memory_request,
            'storage_request': self.storage_request,
            'image_uri': self.image_uri,
            'image_tag': self.image_tag,
            'features_request': self.features_request,
            'gitpuller_targets': [target.to_api_data() for target in
                                  self.gitpuller_targets],
            'configuration_comments': self.configuration_comments
        }


@dataclass
class CourseStatus:
    """
    Data class representing the status of a JupyterHub for a course.
    Maps to the CourseStatus schema from the API.
    """
    id: int
    status: str
    hub_deployed: bool = False
    message: str = ""
    configuration: Optional[CourseConfiguration] = None
    status_added: Optional[datetime] = None
    status_added_by: str = ""
    course: int = 0  # Course ID reference

    STATUS_CHOICES = {
        'requested': 'Requested',
        'blocked': 'Blocked',
        'pending': 'Pending',
        'deployed': 'Deployed',
        'archived': 'Archived',
    }

    def __post_init__(self):
        """
        Validate email if provided.
        """
        if self.status_added_by:
            validator = EmailValidator()
            try:
                validator(self.status_added_by)
            except ValidationError as e:
                raise ValueError(f"Invalid status_added_by email: {e}")

    def get_status_display(self) -> str:
        """
        Get the display name for the status.
        """
        return self.STATUS_CHOICES.get(self.status, self.status)

    def __str__(self):
        return f"Course {self.course} - {self.status} ({self.status_added})"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'CourseStatus':
        """
        Create CourseStatus instance from API response data.
        """
        configuration = None
        if data.get('configuration'):
            configuration = CourseConfiguration.from_api_data(
                data['configuration'])

        return cls(
            id=data['id'],
            status=data['status'],
            hub_deployed=data.get('hub_deployed', False),
            message=data.get('message', ''),
            configuration=configuration,
            status_added=parse_api_datetime(data.get('status_added')),
            status_added_by=data.get('status_added_by', ''),
            course=data.get('course', 0)
        )


@dataclass
class CourseStatusDetail:
    """
    Data class representing detailed course status.
    Maps to the CourseStatusDetail schema from the API.
    """
    id: int
    course: int
    status: str
    hub_deployed: bool = False
    message: str = ""
    configuration: Optional[CourseConfiguration] = None
    status_added: Optional[datetime] = None
    status_added_by: str = ""

    def __str__(self):
        return f"Course {self.course} - {self.status} ({self.status_added})"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'CourseStatusDetail':
        """
        Create CourseStatusDetail instance from API response data.
        """
        configuration = None
        if data.get('configuration'):
            configuration = CourseConfiguration.from_api_data(
                data['configuration'])

        return cls(
            id=data['id'],
            course=data['course'],
            status=data['status'],
            hub_deployed=data.get('hub_deployed', False),
            message=data.get('message', ''),
            configuration=configuration,
            status_added=parse_api_datetime(data.get('status_added')),
            status_added_by=data.get('status_added_by', '')
        )


@dataclass
class Course:
    """
    Data class representing a course that may have a JupyterHub.
    Maps to the Course schema from the API.
    """
    QUARTER_CHOICES = {
        1: 'Winter',
        2: 'Spring',
        3: 'Summer',
        4: 'Autumn',
    }

    id: int
    name: str
    course_year: int
    course_quarter: int
    sis_course_id: str
    hub_url: str
    last_changed: Optional[datetime] = None
    in_admin_courses: bool = False  # Read-only computed field
    latest_status: Optional[CourseStatus] = None  # Read-only computed field
    hub_admins: Optional[List[str]] = None

    def get_quarter_display_name(self) -> str:
        """
        Get the display name for the quarter.
        """
        return self.QUARTER_CHOICES.get(self.course_quarter, 'Unknown')

    def __str__(self):
        return f"{self.name} ({self.sis_course_id})"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Course':
        """
        Create Course instance from API response data.
        """
        latest_status = None
        if data.get('latest_status'):
            latest_status = CourseStatus.from_api_data(data['latest_status'])

        return cls(
            id=data['id'],
            name=data['name'],
            course_year=data['course_year'],
            course_quarter=data['course_quarter'],
            sis_course_id=data['sis_course_id'],
            hub_url=data['hub_url'],
            last_changed=parse_api_datetime(data.get('last_changed')),
            in_admin_courses=data.get('in_admin_courses', False),
            latest_status=latest_status,
            hub_admins=data.get('hub_admins')
        )


@dataclass
class CourseDetail:
    """
    Data class representing detailed course information.
    Maps to the CourseDetail schema from the API.
    """
    id: int
    name: str
    course_year: int
    course_quarter: int
    sis_course_id: str
    hub_url: str
    last_changed: Optional[datetime] = None
    in_admin_courses: bool = False  # Read-only computed field
    statuses: List[CourseStatus] = field(default_factory=list)  # Read-only
    hub_admins: Optional[List[str]] = None

    def get_quarter_display_name(self) -> str:
        """
        Get the display name for the quarter.
        """
        return Course.QUARTER_CHOICES.get(self.course_quarter, 'Unknown')

    def __str__(self):
        return f"{self.name} ({self.sis_course_id})"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'CourseDetail':
        """
        Create CourseDetail instance from API response data.
        """
        statuses = []
        if 'statuses' in data:
            statuses = [CourseStatus.from_api_data(status) for status in
                        data['statuses']]

        return cls(
            id=data['id'],
            name=data['name'],
            course_year=data['course_year'],
            course_quarter=data['course_quarter'],
            sis_course_id=data['sis_course_id'],
            hub_url=data['hub_url'],
            last_changed=parse_api_datetime(data.get('last_changed')),
            in_admin_courses=data.get('in_admin_courses', False),
            statuses=statuses,
            hub_admins=data.get('hub_admins')
        )


# Create/Update schemas for API requests
@dataclass
class CourseCreate:
    """
    Data class for creating courses via API.
    Maps to the CourseCreate schema.
    """
    name: str
    course_year: int
    course_quarter: int
    sis_course_id: str
    hub_url: str = ""

    def to_api_data(self) -> Dict[str, Any]:
        """Convert to API format."""
        return {
            'name': self.name,
            'course_year': self.course_year,
            'course_quarter': self.course_quarter,
            'sis_course_id': self.sis_course_id,
            'hub_url': self.hub_url
        }


@dataclass
class CourseStatusCreate:
    """
    Data class for creating course status via API.
    Maps to the CourseStatusCreate schema.
    """
    course: int
    status: str
    hub_deployed: bool = False
    message: str = ""
    configuration: Optional[CourseConfiguration] = None

    def to_api_data(self) -> Dict[str, Any]:
        """
        Convert to API format.
        """
        data = {
            'course': self.course,
            'status': self.status,
            'hub_deployed': self.hub_deployed,
            'message': self.message
        }
        if self.configuration:
            data['configuration'] = self.configuration.to_api_data()
        return data


@dataclass
class CourseStatusUpdate:
    """
    Data class for updating course status via API.
    Maps to the CourseStatusUpdate schema.
    """
    sis_course_id: str
    status: str
    auto_create: bool = False
    hub_deployed: bool = False
    message: str = ""
    configuration: Optional[CourseConfiguration] = None
    name: str = ""
    course_year: Optional[int] = None
    course_quarter: str = ""
    hub_url: str = ""
    status_added_by: str = ""
    hub_admins: Optional[List[str]] = None

    def to_api_data(self) -> Dict[str, Any]:
        """
        Convert to API format.
        course_quarter & course_year have been temporarily removed as they
        are not included in the BLTI payload currently
        """
        data = {
            'sis_course_id': self.sis_course_id,
            'status': self.status,
            'auto_create': self.auto_create,
            'hub_deployed': self.hub_deployed,
            'message': self.message,
            'name': self.name,
            'hub_url': self.hub_url,
            'status_added_by': self.status_added_by,
            'hub_admins': self.hub_admins
        }
        if self.configuration:
            data['configuration'] = self.configuration.to_api_data()
        return data


# Utility functions
def parse_api_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Parse datetime string from API response.
    """
    if not dt_str:
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))


def serialize_for_api(data_obj) -> Dict[str, Any]:
    """
    Convert dataclass instance to dictionary suitable for API calls.
    """
    if hasattr(data_obj, 'to_api_data'):
        return data_obj.to_api_data()
    elif hasattr(data_obj, '__dataclass_fields__'):
        result = {}
        for field_name, field_obj in data_obj.__dataclass_fields__.items():
            value = getattr(data_obj, field_name)
            if isinstance(value, datetime):
                result[field_name] = value.isoformat()
            elif isinstance(value, list):
                result[field_name] = [
                    serialize_for_api(item) if
                    hasattr(item, '__dataclass_fields__') else
                    item for item in value]
            elif hasattr(value, '__dataclass_fields__'):
                result[field_name] = serialize_for_api(value)
            else:
                result[field_name] = value
        return result
    return data_obj


# Factory functions for creating instances from API responses
class ApiDataFactory:
    """
    Factory class for creating data class instances from API responses.
    """

    @staticmethod
    def create_admin_image(data: Dict[str, Any]) -> AdminImage:
        return AdminImage.from_api_data(data)

    @staticmethod
    def create_admin_course_list(data: Dict[str, Any]) -> AdminCourseList:
        return AdminCourseList.from_api_data(data)

    @staticmethod
    def create_admin_course_detail(data: Dict[str, Any]) -> AdminCourseDetail:
        return AdminCourseDetail.from_api_data(data)

    @staticmethod
    def create_admin_course_settings(
            data: Dict[str, Any]) -> AdminCourseSettings:
        return AdminCourseSettings.from_api_data(data)

    @staticmethod
    def create_course(data: Dict[str, Any]) -> Course:
        return Course.from_api_data(data)

    @staticmethod
    def create_course_detail(data: Dict[str, Any]) -> CourseDetail:
        return CourseDetail.from_api_data(data)

    @staticmethod
    def create_course_configuration(
            data: Dict[str, Any]) -> CourseConfiguration:
        return CourseConfiguration.from_api_data(data)

    @staticmethod
    def create_course_status(
            data: Dict[str, Any]) -> CourseStatus:
        return CourseStatus.from_api_data(data)

    @staticmethod
    def create_course_status_detail(
            data: Dict[str, Any]) -> CourseStatusDetail:
        return CourseStatusDetail.from_api_data(data)

    @staticmethod
    def create_gitpuller_target(data: Dict[str, Any]) -> GitpullerTarget:
        return GitpullerTarget.from_api_data(data)


# Backwards compatibility aliases
AdminImageModel = AdminImage
# Use detail version for backwards compatibility
AdminCourseModel = AdminCourseDetail
AdminCourseSettingsModel = AdminCourseSettings
CourseModel = Course
CourseConfigurationModel = CourseConfiguration
CourseStatusModel = CourseStatus
GitpullerTargetModel = GitpullerTarget

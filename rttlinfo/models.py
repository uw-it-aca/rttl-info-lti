# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.db import models
import json


class Course(models.Model):
    """
    Model representing a course that may have a JupyterHub.
    Maps to the Course schema in the API.
    """
    QUARTER_CHOICES = (
        (1, 'Winter'),
        (2, 'Spring'),
        (3, 'Summer'),
        (4, 'Autumn'),
    )

    name = models.CharField(max_length=255)
    course_year = models.IntegerField()
    course_quarter = models.IntegerField(choices=QUARTER_CHOICES)
    sis_course_id = models.CharField(max_length=255, unique=True)
    hub_url = models.URLField(blank=True, null=True)
    last_changed = models.DateTimeField(auto_now=True)

    @property
    def in_admin_courses(self):
        """Return True if this course exists in the admin courses."""
        # This would typically query the API or check against AdminCourse
        # For now, just placeholder logic
        return AdminCourse.objects.filter(sis_course_id=self.sis_course_id).exists()

    @property
    def latest_status(self):
        """Return the most recent status for this course."""
        return self.coursestatus_set.order_by('-status_added').first()

    def __str__(self):
        return f"{self.name} ({self.sis_course_id})"


class CourseStatus(models.Model):
    """
    Model representing the status of a JupyterHub for a course.
    Maps to the CourseStatus schema in the API.
    """
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('provisioning', 'Provisioning'),
        ('ready', 'Ready'),
        ('error', 'Error'),
        ('deleted', 'Deleted'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES)
    hub_deployed = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    configuration = models.TextField(blank=True)  # Stored as JSON
    status_added = models.DateTimeField(auto_now_add=True)

    def get_configuration(self):
        """Get the configuration as a dictionary."""
        if not self.configuration:
            return {}
        return json.loads(self.configuration)

    def set_configuration(self, config_dict):
        """Set the configuration from a dictionary."""
        self.configuration = json.dumps(config_dict)

    def __str__(self):
        return f"{self.course.name} - {self.status} ({self.status_added})"


class AdminImage(models.Model):
    """
    Model representing a Docker image available for JupyterHub.
    Maps to the AdminImage schema in the API.
    """
    repo = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.repo}:{self.tag})"


class AdminCourse(models.Model):
    """
    Model representing an admin course configuration.
    This is a read-only representation of courses from the admin API.
    Maps to the AdminCourseList and AdminCourseDetail schemas.
    """
    key = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    sis_course_id = models.CharField(max_length=255, unique=True)
    hub_status = models.CharField(max_length=32)
    hub_url = models.URLField(blank=True, null=True)
    hub_token = models.CharField(max_length=255, blank=True)
    last_changed = models.DateTimeField(auto_now=True)
    welcome_email_sent = models.BooleanField(default=False)
    code = models.CharField(max_length=255, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.sis_course_id})"


class AdminCourseSettings(models.Model):
    """
    Model representing JupyterHub settings for an admin course.
    Maps to the AdminCourseSettings schema in the API.
    """
    course = models.OneToOneField(AdminCourse, on_delete=models.CASCADE, related_name='settings')
    image = models.ForeignKey(AdminImage, on_delete=models.SET_NULL, null=True, blank=True)
    storage_capacity = models.CharField(max_length=32, default="1Gi")
    cpu_request = models.CharField(max_length=32, default="0.5")
    cpu_limit = models.CharField(max_length=32, default="1")
    memory_request = models.CharField(max_length=32, default="512Mi")
    memory_limit = models.CharField(max_length=32, default="1Gi")
    lab_ui = models.BooleanField(default=True)
    placeholder_count = models.IntegerField(default=0)
    cull_time = models.IntegerField(default=3600)  # seconds
    spawner = models.CharField(max_length=255, default="kubespawner")
    image_puller_enabled = models.BooleanField(default=True)
    image_tag = models.CharField(max_length=255, blank=True, null=True)
    feature_nfs = models.BooleanField(default=False)
    feature_binderhub = models.BooleanField(default=False)
    feature_nocanvas = models.BooleanField(default=False)
    feature_oidcauth = models.BooleanField(default=False)

    def __str__(self):
        return f"Settings for {self.course.name}"


class AdminCourseExtraEnv(models.Model):
    """
    Model representing additional environment variables for a JupyterHub.
    Maps to the AdminCourseExtraEnv schema in the API.
    """
    settings = models.ForeignKey(AdminCourseSettings, on_delete=models.CASCADE, related_name='extra_envs')
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.key}={self.value}"


class AdminCourseGitPullerTarget(models.Model):
    """
    Model representing git-puller targets for a JupyterHub.
    Maps to the AdminCourseGitPullerTarget schema in the API.
    """
    settings = models.ForeignKey(AdminCourseSettings, on_delete=models.CASCADE, related_name='git_puller_targets')
    key = models.CharField(max_length=255)
    repo = models.URLField()
    branch = models.CharField(max_length=255, default="main")
    target_dir = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.key}: {self.repo}@{self.branch} -> {self.target_dir}"
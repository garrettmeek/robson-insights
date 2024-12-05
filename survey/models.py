from django.db import models
from django.utils import timezone

from users.models import Group, User


class Entry(models.Model):
    CLASSIFICATIONS = [
    ("1", "Group 1"),
    ("2", "Group 2"),
    ("3", "Group 3"),
    ("4", "Group 4"),
    ("5.1", "Group 5.1"),
    ("5.2", "Group 5.2"),
    ("6", "Group 6"),
    ("7", "Group 7"),
    ("8", "Group 8"),
    ("9", "Group 9"),
    ("10", "Group 10"),
]
    classification = models.CharField(
        choices=CLASSIFICATIONS,
        max_length=100,
    )
    user = models.ForeignKey(
        null=True,
        blank=True,
        to=User,
        on_delete=models.SET_NULL,
    )
    groups = models.ManyToManyField(Group, related_name='entries')
    csection = models.BooleanField(
        default=False,
    )
    date = models.DateTimeField(
        default=timezone.now,
    )

    def __str__(self):
        return f'{self.pk} {self.classification} {self.user}'

    class Meta:
        verbose_name_plural = "Entries"


class Filter(models.Model):
    name = models.CharField(
        max_length=100,
    )
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
    )
    groups = models.ManyToManyField(
        to=Group,
        related_name='filters',
        blank=True,
    )

    def __str__(self):
        group_names = ', '.join([group.name for group in self.groups.all()])
        return f'{self.user.username} - Groups: {group_names} {self.pk}'




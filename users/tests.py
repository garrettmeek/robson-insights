from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Group, UserProfile

class TogglePermissionsViewTests(APITestCase):

    def setUp(self):
 
        self.admin_user = User.objects.create_user(username='admin', password='adminpass')
        self.regular_user = User.objects.create_user(username='regular', password='regularpass')
        self.target_user = User.objects.create_user(username='target', password='targetpass')

       
        self.group = Group.objects.create(name='Test Group')

      
        UserProfile.objects.create(user=self.admin_user, group=self.group, is_admin=True)
        UserProfile.objects.create(user=self.regular_user, group=self.group)
        UserProfile.objects.create(user=self.target_user, group=self.group)

      
        self.admin_token = self.client.post('/login/', {'username': 'admin', 'password': 'adminpass'}).data['token']
        self.regular_token = self.client.post('/login/', {'username': 'regular', 'password': 'regularpass'}).data['token']

      
        self.url = reverse('users:toggle-permissions')

    def test_admin_can_toggle_permissions(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token)
        data = {
            'username': 'target',
            'group_id': self.group.id,
            'toggle_add': True,
            'toggle_view': True
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)

      
        target_profile = UserProfile.objects.get(user__username='target', group=self.group)
        self.assertTrue(target_profile.can_add)
        self.assertFalse(target_profile.can_view)

    def test_non_admin_cannot_toggle_permissions(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.regular_token)
        data = {
            'username': 'target',
            'group_id': self.group.id,
            'toggle_add': True,
            'toggle_view': True
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)

    def test_toggle_permissions_user_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token)
        data = {
            'username': 'nonexistent',
            'group_id': self.group.id,
            'toggle_add': True,
            'toggle_view': True
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_toggle_permissions_group_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token)
        data = {
            'username': 'target',
            'group_id': 9999,  
            'toggle_add': True,
            'toggle_view': True
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

class RemoveUserFromGroupTests(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='adminpass')
        self.member_user = User.objects.create_user(username='member', password='memberpass')
        self.other_user = User.objects.create_user(username='other', password='otherpass')

        self.group = Group.objects.create(name='Test Group')

        UserProfile.objects.create(user=self.admin_user, group=self.group, is_admin=True)
        UserProfile.objects.create(user=self.member_user, group=self.group, is_admin=False)

        self.admin_token = self.client.post('/login/', {'username': 'admin', 'password': 'adminpass'}).data['token']
        self.member_token = self.client.post('/login/', {'username': 'member', 'password': 'memberpass'}).data['token']
        self.other_token = self.client.post('/login/', {'username': 'other', 'password': 'otherpass'}).data['token']

        self.url = reverse('users:remove-user-from-group')

    def test_admin_can_remove_member(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token)
        data = {
            'username': 'member',
            'group_id': self.group.id
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)

        self.assertFalse(UserProfile.objects.filter(user=self.member_user, group=self.group).exists())

    def test_non_admin_cannot_remove_member(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.member_token)
        data = {
            'username': 'other',
            'group_id': self.group.id
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)

    def test_remove_user_not_in_group(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token)
        data = {
            'username': 'other',
            'group_id': self.group.id
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_remove_user_from_nonexistent_group(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token)
        data = {
            'username': 'member',
            'group_id': 9999  
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
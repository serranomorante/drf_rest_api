from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """ test publicly available ingredients api """
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """ test that login is required to access the endpoint """
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """ test the private ingredient API """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@londo.com",
            "jaysfds72"
        )

        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """ test retrieving a set of ingredients """
        Ingredient.objects.create(user=self.user, name="Kale")
        Ingredient.objects.create(user=self.user, name="Salt")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """ test that only ingredient for authenticated users are returned """
        user2 = get_user_model().objects.create_user(
            'london@dev.com',
            'hsvsgdaa7'
        )

        Ingredient.objects.create(user=user2, name="Vinegar")
        ingredient = Ingredient.objects.create(user=self.user, name="Tumeric")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_ingredient_successful(self):
        """ test create a new ingredient """
        payload = {
            "name": 'Cabbage'
        }

        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """ test creating invalid ingredient fails """
        payload = {
            "name": ""
        }
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

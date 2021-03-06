from rest_framework import routers
from poetry import views

router = routers.DefaultRouter()
router.register('authors', views.AuthorViewSet, 'author')
urlpatterns = router.urls

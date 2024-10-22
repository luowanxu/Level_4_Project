# travelapp/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# API configurations
GEODB_HOST = "wft-geo-db.p.rapidapi.com"
GOOGLE_MAPS_HOST = "google-map-places.p.rapidapi.com"

@csrf_exempt
def search_city(request):
    """使用 GeoDB API 进行城市搜索和联想"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            search_text = data.get('searchText', '')
            
            if not search_text or len(search_text) < 2:
                return JsonResponse({'error': 'Search text too short'}, status=400)

            headers = {
                "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
                "X-RapidAPI-Host": GEODB_HOST
            }

            response = requests.get(
                f'https://{GEODB_HOST}/v1/geo/cities',
                headers=headers,
                params={
                    'namePrefix': search_text,
                    'countryIds': 'GB',
                    'limit': 5,
                    'types': 'CITY'
                }
            )
            
            response.raise_for_status()
            cities_data = response.json()
            
            logger.info(f"Found {len(cities_data.get('data', []))} cities matching '{search_text}'")
            
            return JsonResponse(cities_data)
            
        except Exception as e:
            logger.error(f"Error in search_city: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def get_city_places(request):
    """使用 Google Maps Places API 获取城市地点信息"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            city_name = data.get('cityName', '')
            
            logger.info(f"Searching places for city: {city_name}")
            
            if not city_name:
                return JsonResponse({'error': 'City name is required'}, status=400)

            headers = {
                "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
                "X-RapidAPI-Host": GOOGLE_MAPS_HOST
            }

            # 首先获取城市的地理编码
            geocode_url = f"https://{GOOGLE_MAPS_HOST}/maps/api/geocode/json"
            geocode_params = {
                "address": f"{city_name}, UK",
                "language": "en"
            }
            
            geocode_response = requests.get(
                geocode_url,
                headers=headers,
                params=geocode_params
            )
            
            if geocode_response.status_code != 200:
                logger.error(f"Geocoding failed: {geocode_response.text}")
                return JsonResponse({'error': 'Failed to locate city'}, status=500)

            geocode_data = geocode_response.json()
            if not geocode_data.get('results'):
                return JsonResponse({'error': 'City not found'}, status=404)

            # 获取城市的位置坐标
            location = geocode_data['results'][0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            
            logger.info(f"Found coordinates for {city_name}: {lat}, {lng}")

            places_data = {
                'restaurants': [],
                'attractions': [],
                'hotels': []
            }

            # 使用 Places Nearby Search 获取各类地点
            nearby_url = f"https://{GOOGLE_MAPS_HOST}/maps/api/place/nearbysearch/json"
            
            # 获取餐厅
            restaurant_params = {
                "location": f"{lat},{lng}",
                "radius": "5000",
                "type": "restaurant",
                "language": "en"
            }
            
            try:
                restaurants_response = requests.get(
                    nearby_url,
                    headers=headers,
                    params=restaurant_params
                )
                if restaurants_response.status_code == 200:
                    restaurants_data = restaurants_response.json()
                    places_data['restaurants'] = restaurants_data.get('results', [])
                    logger.info(f"Found {len(places_data['restaurants'])} restaurants")
                else:
                    logger.error(f"Restaurant search failed: {restaurants_response.text}")
            except Exception as e:
                logger.error(f"Error fetching restaurants: {str(e)}")

            # 获取景点
            attraction_params = {
                "location": f"{lat},{lng}",
                "radius": "5000",
                "type": "tourist_attraction",
                "language": "en"
            }
            
            try:
                attractions_response = requests.get(
                    nearby_url,
                    headers=headers,
                    params=attraction_params
                )
                if attractions_response.status_code == 200:
                    attractions_data = attractions_response.json()
                    places_data['attractions'] = attractions_data.get('results', [])
                    logger.info(f"Found {len(places_data['attractions'])} attractions")
                else:
                    logger.error(f"Attractions search failed: {attractions_response.text}")
            except Exception as e:
                logger.error(f"Error fetching attractions: {str(e)}")

            # 获取酒店
            hotel_params = {
                "location": f"{lat},{lng}",
                "radius": "5000",
                "type": "lodging",
                "language": "en"
            }
            
            try:
                hotels_response = requests.get(
                    nearby_url,
                    headers=headers,
                    params=hotel_params
                )
                if hotels_response.status_code == 200:
                    hotels_data = hotels_response.json()
                    places_data['hotels'] = hotels_data.get('results', [])
                    logger.info(f"Found {len(places_data['hotels'])} hotels")
                else:
                    logger.error(f"Hotels search failed: {hotels_response.text}")
            except Exception as e:
                logger.error(f"Error fetching hotels: {str(e)}")

            # 检查是否获取到任何数据
            if not any(places_data.values()):
                logger.error("No data found in any category")
                return JsonResponse({
                    'error': f'No places found for {city_name}'
                }, status=404)

            # 记录成功信息
            logger.info(f"Successfully retrieved data for {city_name}")
            return JsonResponse(places_data)

        except Exception as e:
            logger.error(f"Unexpected error in get_city_places: {str(e)}")
            return JsonResponse({
                'error': f'An unexpected error occurred: {str(e)}'
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
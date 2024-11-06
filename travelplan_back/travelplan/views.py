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

            # 处理城市名称，替换空格为加号
            formatted_city_name = city_name.replace(' ', '+')

            # 获取城市的地理编码
            geocode_url = f"https://{GOOGLE_MAPS_HOST}/maps/api/geocode/json"
            geocode_params = {
                "address": f"{formatted_city_name},+UK",
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

            location = geocode_data['results'][0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            
            logger.info(f"Found coordinates: {lat}, {lng}")

            places_data = {
                'restaurants': [],
                'attractions': [],
                'hotels': []
            }

            nearby_url = f"https://{GOOGLE_MAPS_HOST}/maps/api/place/nearbysearch/json"

            # 搜索餐厅
            try:
                restaurants_params = {
                    "location": f"{lat},{lng}",
                    "radius": "5000",
                    "type": "restaurant",
                    "keyword": "restaurant",
                    "language": "en"
                }
                restaurants_response = requests.get(
                    nearby_url,
                    headers=headers,
                    params=restaurants_params
                )
                if restaurants_response.status_code == 200:
                    restaurants_data = restaurants_response.json().get('results', [])
                    filtered_restaurants = [
                        place for place in restaurants_data
                        if ('restaurant' in place.get('types', []) and 
                            not any(t in place.get('types', []) for t in ['lodging', 'hotel']))
                    ]
                    places_data['restaurants'] = filtered_restaurants
                    logger.info(f"Found {len(filtered_restaurants)} restaurants after filtering")
                else:
                    logger.error(f"Restaurant search failed: {restaurants_response.text}")
            except Exception as e:
                logger.error(f"Error fetching restaurants: {str(e)}")

            # 搜索景点
            try:
                attractions_params = {
                    "location": f"{lat},{lng}",
                    "radius": "5000",
                    "type": "tourist_attraction",
                    "language": "en"
                }
                attractions_response = requests.get(
                    nearby_url,
                    headers=headers,
                    params=attractions_params
                )
                if attractions_response.status_code == 200:
                    attractions_data = attractions_response.json().get('results', [])
                    filtered_attractions = [
                        place for place in attractions_data
                        if not any(t in place.get('types', []) for t in ['lodging', 'restaurant'])
                    ]
                    places_data['attractions'] = filtered_attractions
                    logger.info(f"Found {len(filtered_attractions)} attractions after filtering")
                else:
                    logger.error(f"Attractions search failed: {attractions_response.text}")
            except Exception as e:
                logger.error(f"Error fetching attractions: {str(e)}")

            # 搜索酒店
            try:
                hotels_params = {
                    "location": f"{lat},{lng}",
                    "radius": "5000",
                    "type": "lodging",
                    "language": "en"
                }
                hotels_response = requests.get(
                    nearby_url,
                    headers=headers,
                    params=hotels_params
                )
                if hotels_response.status_code == 200:
                    hotels_data = hotels_response.json().get('results', [])
                    filtered_hotels = [
                        place for place in hotels_data
                        if 'lodging' in place.get('types', [])
                    ]
                    places_data['hotels'] = filtered_hotels
                    logger.info(f"Found {len(filtered_hotels)} hotels after filtering")
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

            # 记录每个类别的结果数量
            for category, items in places_data.items():
                logger.info(f"Category {category} has {len(items)} items")
                if items:
                    logger.info(f"Sample types in {category}: {items[0].get('types', [])}")

            return JsonResponse(places_data)

        except Exception as e:
            logger.error(f"Unexpected error in get_city_places: {str(e)}")
            return JsonResponse({
                'error': f'An unexpected error occurred: {str(e)}'
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
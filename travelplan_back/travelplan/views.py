# travelapp/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import logging
from django.conf import settings
from sklearn.cluster import KMeans
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# API configurations
GEODB_HOST = "wft-geo-db.p.rapidapi.com"
GOOGLE_MAPS_HOST = "google-map-places.p.rapidapi.com"

@csrf_exempt
def search_city(request):
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

            # 查看API文档，我发现可以使用不同的端点来搜索地理位置
            response = requests.get(
                f'https://{GEODB_HOST}/v1/geo/places',  # 使用 places 端点而不是 cities
                headers=headers,
                params={
                    'namePrefix': search_text,
                    'limit': 10,
                    'sort': '-population',
                    # 注意：places 端点支持更广泛的地点类型，包括岛屿
                }
            )
            
            if response.status_code == 200:
                places_data = response.json()
                if 'data' in places_data:
                    for item in places_data['data']:
                        location_type = item.get('type', 'UNKNOWN')
                        # 扩展类型映射
                        type_mapping = {
                            'CITY': 'City',
                            'ADM2': 'District',
                            'ISL': 'Island',  # 注意：places API中岛屿的类型代码可能是 'ISL'
                            'ISLS': 'Islands',
                            'ADM1': 'Province/State',
                            'CONT': 'Continent',
                            'RGN': 'Region'
                        }
                        type_description = type_mapping.get(location_type, location_type)
                        
                        # 构建标签
                        name = item.get('name', '')
                        region = item.get('region', '')
                        country = item.get('country', '')
                        
                        label_parts = [name]
                        if type_description != 'City':  # 如果不是城市，添加类型说明
                            label_parts.append(f"({type_description})")
                        if region:
                            label_parts.append(region)
                        if country:
                            label_parts.append(country)
                        
                        item['type'] = type_description
                        item['label'] = ', '.join(filter(None, label_parts))
                
                return JsonResponse(places_data)
            else:
                logger.error(f"Search failed with status {response.status_code}: {response.text}")
                return JsonResponse({
                    'error': 'Search failed', 
                    'details': response.text
                }, status=response.status_code)
            
        except Exception as e:
            logger.error(f"Error in search_city: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def get_city_places(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            city_name = data.get('cityName', '')
            region = data.get('region', '')
            country = data.get('country', '')
            
            logger.info(f"Searching places for location: {city_name}, {region}, {country}")
            
            if not city_name:
                return JsonResponse({'error': 'Location name is required'}, status=400)

            headers = {
                "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
                "X-RapidAPI-Host": GOOGLE_MAPS_HOST
            }

            # 构建完整的地址字符串
            address_parts = [part for part in [city_name, region, country] if part]
            full_address = ', '.join(address_parts)
            formatted_address = full_address.replace(' ', '+')

            # 获取地理编码
            geocode_url = f"https://{GOOGLE_MAPS_HOST}/maps/api/geocode/json"
            geocode_params = {
                "address": formatted_address,
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





@csrf_exempt
def cluster_places(request):


    def format_time(hour):
        """格式化时间为12小时制"""
        if hour == 0 or hour == 12:
            return f"12:00 {'AM' if hour == 0 else 'PM'}"
        elif hour > 12:
            return f"{hour-12}:00 PM"
        else:
            return f"{hour}:00 AM"
        


    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            places = data.get('places', [])
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            
            if not places:
                return JsonResponse({'error': 'No places provided'}, status=400)
                
            if not start_date or not end_date:
                return JsonResponse({'error': 'Date range is required'}, status=400)
                
            # 计算天数
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            num_days = (end - start).days + 1
            
            if len(places) < num_days:
                return JsonResponse({
                    'error': f'Cannot create {num_days} days itinerary with only {len(places)} places'
                }, status=400)

            # 提取坐标进行聚类
            coordinates = np.array([[
                place['geometry']['location']['lat'],
                place['geometry']['location']['lng']
            ] for place in places])
            
            # 执行聚类
            kmeans = KMeans(n_clusters=num_days, random_state=42)
            clusters = kmeans.fit_predict(coordinates)
            
            # 组织结果
            clustered_places = [[] for _ in range(num_days)]
            for place, cluster_id in zip(places, clusters):
                clustered_places[cluster_id].append(place)
            
            # 生成时间安排
            START_HOUR = 9  # 上午9点开始
            VISIT_DURATION = 2  # 每个地点2小时
            
            timeline_events = []
            for day_index, day_places in enumerate(clustered_places):
                current_hour = START_HOUR
                for place_index, place in enumerate(day_places):
                    if current_hour >= 20:  # 晚上8点后不再安排
                        continue
                        
                    event = {
                        'id': f'{day_index}-{place_index}',
                        'title': place['name'],
                        'startTime': format_time(current_hour),
                        'endTime': format_time(current_hour + VISIT_DURATION),
                        'day': day_index,
                        'position': {
                            'x': (current_hour - START_HOUR) * 120,  # 120是CELL_WIDTH
                            'y': day_index * 80  # 80是CELL_HEIGHT
                        },
                        'duration': VISIT_DURATION,
                        'place': place
                    }
                    
                    timeline_events.append(event)
                    current_hour += VISIT_DURATION

            return JsonResponse({
                'success': True,
                'events': timeline_events,
                'clusters': clustered_places
            })
            
        except Exception as e:
            logger.error(f"Error in cluster_places: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)
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
from icalendar import Calendar, Event
from django.http import HttpResponse


logger = logging.getLogger(__name__)

# API configurations
GEODB_HOST = "wft-geo-db.p.rapidapi.com"
GOOGLE_MAPS_HOST = "google-map-places.p.rapidapi.com"
TRUEWAY_MATRIX_HOST = "trueway-matrix.p.rapidapi.com"


from .services import schedule_service  # 从 __init__.py 导入实例



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














async def _fetch_places(places_data, lat, lng, place_type, category, headers):
    """异步获取地点数据"""
    try:
        response = await sync_to_async(requests.get)(
            f"https://{GOOGLE_MAPS_HOST}/maps/api/place/nearbysearch/json",
            headers=headers,
            params={
                "location": f"{lat},{lng}",
                "radius": "5000",
                "type": place_type,
                "language": "en"
            }
        )
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            places_data[category] = [
                place for place in results
                if place_type in place.get('types', [])
            ]
            logger.info(f"Found {len(places_data[category])} {category}")
    except Exception as e:
        logger.error(f"Error fetching {category}: {str(e)}")


@csrf_exempt
async def cluster_places(request):
    """生成行程endpoint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            places = data.get('places', [])
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            transport_mode = data.get('transportMode', 'driving')
            
            if not all([places, start_date, end_date]):
                return JsonResponse({
                    'error': 'Missing required parameters'
                }, status=400)

            # 使用schedule_service生成行程
            result = await schedule_service.generate_schedule(
                places=places,
                start_date=start_date,
                end_date=end_date,
                transport_mode=transport_mode
            )

            if result['success']:
                return JsonResponse(result)
            else:
                return JsonResponse(result, status=500)

        except Exception as e:
            logger.error(f"Error in cluster_places: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
async def update_schedule(request):
    """更新行程endpoint（用于手动模式）"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            events = data.get('events', [])
            transport_mode = data.get('transportMode', 'driving')

            if not events:
                return JsonResponse({
                    'error': 'No events provided'
                }, status=400)

            # 使用schedule_service更新行程
            result = await schedule_service.update_schedule(
                events=events,
                transport_mode=transport_mode
            )

            if result['success']:
                return JsonResponse(result)
            else:
                return JsonResponse(result, status=500)

        except Exception as e:
            logger.error(f"Error in update_schedule: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
async def optimize_route(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            events = data.get('events', [])
            transport_mode = data.get('transportMode', 'driving')

            # 使用与cluster_places相同的逻辑重新生成最优日程
            result = await schedule_service.generate_schedule(
                places=[event['place'] for event in events if event.get('type') == 'place'],
                start_date=data.get('startDate'),  # 需要从前端传入
                end_date=data.get('endDate'),      # 需要从前端传入
                transport_mode=transport_mode
            )

            if result['success']:
                return JsonResponse(result)
            else:
                return JsonResponse(result, status=500)

        except Exception as e:
            logger.error(f"Error in optimize_route: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)





@csrf_exempt
def export_calendar(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            events = data.get('events', [])
            
            cal = Calendar()
            cal.add('prodid', '-//Trip Planner//TripSchedule//EN')
            cal.add('version', '2.0')
            
            # 使用传入的日期作为基准
            for event in events:
                if event.get('type') != 'place':  # 只处理地点事件
                    continue
                    
                cal_event = Event()
                cal_event.add('summary', event['title'])
                
                # 使用事件的day属性和时间来构建完整的日期时间
                day_number = int(event['day'])
                if event.get('startTime') and event.get('endTime'):
                    start_time = datetime.strptime(event['startTime'], '%I:%M %p')
                    end_time = datetime.strptime(event['endTime'], '%I:%M %p')
                    
                    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    event_date = base_date + timedelta(days=day_number)
                    
                    start_datetime = event_date.replace(
                        hour=start_time.hour,
                        minute=start_time.minute
                    )
                    end_datetime = event_date.replace(
                        hour=end_time.hour,
                        minute=end_time.minute
                    )
                    
                    cal_event.add('dtstart', start_datetime)
                    cal_event.add('dtend', end_datetime)
                
                    if event.get('place'):
                        cal_event.add('location', event['place'].get('vicinity', ''))
                        cal_event.add('description', f"Rating: {event['place'].get('rating', 'N/A')}")
                    
                    cal.add_component(cal_event)
            
            response = HttpResponse(cal.to_ical(), content_type='text/calendar')
            response['Content-Disposition'] = 'attachment; filename=trip-schedule.ics'
            return response
            
        except Exception as e:
            logger.error(f"Error exporting calendar: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
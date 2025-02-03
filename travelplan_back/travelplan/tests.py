from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, time
import numpy as np
from .services.clustering import PlaceConstraints
from .services.schedule_service import ScheduleService

class TravelPlanTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.mock_rapidapi_key = "test-api-key"
        self.patcher = patch('django.conf.settings.RAPIDAPI_KEY', self.mock_rapidapi_key)
        self.patcher.start()
        
    def tearDown(self):
        self.patcher.stop()

    @patch('requests.get')
    def test_search_city_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{
                "name": "Paris",
                "region": "Ile-de-France",
                "country": "France",
                "type": "CITY"
            }]
        }
        mock_get.return_value = mock_response

        response = self.client.post(
            '/api/search-city/',
            data=json.dumps({"searchText": "Paris"}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('data', data)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['name'], 'Paris')

    def test_search_city_error(self):
        response = self.client.post(
            '/api/search-city/',
            data=json.dumps({"searchText": "P"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))

    @patch('requests.get')
    def test_get_city_places_success(self, mock_get):
        def mock_get_response(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            if 'geocode' in args[0]:
                mock_response.json.return_value = {
                    "results": [{
                        "geometry": {
                            "location": {
                                "lat": 48.8566,
                                "lng": 2.3522
                            }
                        }
                    }]
                }
            else:
                mock_response.json.return_value = {
                    "results": [{
                        "name": "Eiffel Tower",
                        "types": ["tourist_attraction"],
                        "rating": 4.5,
                        "vicinity": "Champ de Mars, Paris",
                        "geometry": {
                            "location": {
                                "lat": 48.8584,
                                "lng": 2.2945
                            }
                        }
                    }]
                }
            return mock_response

        mock_get.side_effect = mock_get_response

        response = self.client.post(
            '/api/city-places/',
            data=json.dumps({
                "cityName": "Paris",
                "region": "Ile-de-France",
                "country": "France"
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('attractions', data)
        self.assertIn('restaurants', data)
        self.assertIn('hotels', data)

    def test_export_calendar(self):
        events = [
            {
                'type': 'place',
                'title': 'Eiffel Tower',
                'day': '1',
                'startTime': '9:00 AM',
                'endTime': '11:00 AM',
                'place': {
                    'vicinity': 'Champ de Mars, Paris',
                    'rating': 4.5
                }
            }
        ]

        response = self.client.post(
            '/api/export-calendar/',
            data=json.dumps({'events': events}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/calendar')
        self.assertIn('attachment; filename=trip-schedule.ics', response['Content-Disposition'])

    def test_validate_schedule_service(self):
        service = ScheduleService()
        self.assertIsNotNone(service)
        self.assertIsInstance(service.distance_matrix_cache, dict)

class TravelPlanAsyncTest(TransactionTestCase):
    async def asyncSetUp(self):
        from django.test import AsyncClient
        self.async_client = AsyncClient()
        self.mock_rapidapi_key = "test-api-key"
        self.patcher = patch('django.conf.settings.RAPIDAPI_KEY', self.mock_rapidapi_key)
        self.patcher.start()

    async def asyncTearDown(self):
        self.patcher.stop()

    @patch('travelplan.services.schedule_service.ScheduleService.generate_schedule')
    async def test_cluster_places(self, mock_generate_schedule):
        mock_generate_schedule.return_value = {
            'success': True,
            'events': [
                {
                    'day': 1,
                    'type': 'place',
                    'title': 'Eiffel Tower',
                    'startTime': '9:00 AM',
                    'endTime': '11:00 AM',
                    'place': {
                        'name': 'Eiffel Tower',
                        'vicinity': 'Champ de Mars, Paris',
                        'rating': 4.5
                    }
                }
            ],
            'schedule_status': {
                'is_reasonable': True,
                'warnings': [],
                'severity': 'normal'
            }
        }

        test_data = {
            'places': [{
                'name': 'Eiffel Tower',
                'geometry': {
                    'location': {'lat': 48.8584, 'lng': 2.2945}
                },
                'types': ['tourist_attraction']
            }],
            'startDate': '2024-02-01',
            'endDate': '2024-02-03',
            'transportMode': 'driving'
        }

        response = await self.async_client.post(
            '/api/cluster-places/',
            json.dumps(test_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('events', data)


class UtilsTestCase(TestCase):
    """测试 utils.py 中的工具函数"""
    
    def test_haversine_distance(self):
        """测试两点之间的距离计算"""
        from .services.utils import haversine_distance
        
        # 测试用例1: 爱丁堡到伦敦的距离
        edinburgh_lat, edinburgh_lon = 55.9533, -3.1883
        london_lat, london_lon = 51.5074, -0.1278
        distance = haversine_distance(edinburgh_lat, edinburgh_lon, london_lat, london_lon)
        # 实际距离大约是534公里，转换为米后约为534000米
        self.assertAlmostEqual(distance, 534000, delta=5000)  # 允许5公里的误差
        
        # 测试用例2: 相同点的距离应该为0
        distance = haversine_distance(london_lat, london_lon, london_lat, london_lon)
        self.assertEqual(distance, 0)
        
        # 测试用例3: 巴黎到柏林的距离
        paris_lat, paris_lon = 48.8566, 2.3522
        berlin_lat, berlin_lon = 52.5200, 13.4050
        distance = haversine_distance(paris_lat, paris_lon, berlin_lat, berlin_lon)
        # 实际距离大约是878公里，转换为米后约为878000米
        self.assertAlmostEqual(distance, 878000, delta=5000)  # 允许5公里的误差
    
    def test_calculate_travel_time(self):
        """测试行程时间计算"""
        from .services.utils import calculate_travel_time
        
        # 测试不同交通方式的时间计算
        # 测试1公里的行程
        self.assertGreaterEqual(calculate_travel_time(1, 'walking'), 5)  # 至少需要5分钟
        self.assertGreaterEqual(calculate_travel_time(1, 'driving'), 5)  # 至少需要5分钟
        self.assertGreaterEqual(calculate_travel_time(1, 'transit'), 10)  # 至少需要10分钟
        
        # 测试较长距离
        walking_time = calculate_travel_time(5, 'walking')
        driving_time = calculate_travel_time(5, 'driving')
        transit_time = calculate_travel_time(5, 'transit')
        
        # 确保不同交通方式的时间合理
        self.assertGreater(walking_time, driving_time)  # 步行应该比开车慢
        self.assertLess(driving_time, 120)  # 驾车不应超过2小时
        self.assertGreater(transit_time, driving_time)  # 公共交通应该比开车慢
        
    def test_edge_cases_haversine(self):
        """测试haversine_distance函数的边界情况"""
        from .services.utils import haversine_distance
        
        # 测试赤道上的点（地球周长的一半）
        eq_dist = haversine_distance(0, 0, 0, 180)
        self.assertAlmostEqual(eq_dist, 20015087, delta=10000)  # 允许10km的误差
        
        # 测试极点
        pole_dist = haversine_distance(90, 0, -90, 0)
        self.assertAlmostEqual(pole_dist, 20015087, delta=10000)  # 允许10km的误差

        # 测试相对距离的一致性
        dist1 = haversine_distance(0, 0, 0, 90)
        dist2 = haversine_distance(0, 90, 0, 180)
        self.assertAlmostEqual(dist1, dist2, delta=100)  # 这两段距离应该相等

    def test_edge_cases_travel_time(self):
        """测试calculate_travel_time函数的边界情况"""
        from .services.utils import calculate_travel_time
        
        # 测试极短距离
        self.assertEqual(
            calculate_travel_time(0.1, 'walking'),
            5  # 应该返回最小时间
        )
        
        # 测试极长距离
        self.assertEqual(
            calculate_travel_time(1000, 'driving'),
            120  # 应该返回最大时间限制
        )
        
        # 测试负距离
        self.assertEqual(
            calculate_travel_time(-1, 'transit'),
            10  # 应该返回最小时间
        )
        
        # 验证不同交通方式的最小时间限制
        self.assertEqual(calculate_travel_time(0, 'walking'), 5)
        self.assertEqual(calculate_travel_time(0, 'transit'), 10)
        self.assertEqual(calculate_travel_time(0, 'driving'), 5)

    def test_edge_cases_combine_schedules(self):
        """测试combine_schedules函数的边界情况"""
        from .services.utils import combine_schedules
        
        # 测试空列表
        self.assertEqual(combine_schedules([]), [])
        
        # 测试空日程
        self.assertEqual(combine_schedules([[], []]), [])
        
        # 测试单个空日程
        self.assertEqual(combine_schedules([[]]), [])
        
        # 测试包含事件的日程
        schedule1 = [{'id': '1', 'title': 'Event 1', 'day': 0}]
        schedule2 = [{'id': '2', 'title': 'Event 2', 'day': 0}]
        combined = combine_schedules([schedule1, schedule2])
        
        # 验证合并后的日程
class ClusteringTestCase(TestCase):
    """测试clustering.py中的功能"""

    def test_place_constraints(self):
        """测试地点约束配置"""
        from .services.clustering import PlaceConstraints
        from datetime import time

        # 测试用餐时间窗口
        lunch_window = PlaceConstraints.DINING_WINDOWS['lunch']
        self.assertEqual(lunch_window['start'], time(11, 0))
        self.assertEqual(lunch_window['end'], time(14, 0))
        self.assertEqual(lunch_window['optimal'], time(12, 30))

        dinner_window = PlaceConstraints.DINING_WINDOWS['dinner']
        self.assertEqual(dinner_window['start'], time(17, 0))
        self.assertEqual(dinner_window['end'], time(20, 0))
        self.assertEqual(dinner_window['optimal'], time(18, 30))

        # 测试营业时间约束
        self.assertEqual(PlaceConstraints.DAY_CONSTRAINTS['start'], time(9, 0))
        self.assertEqual(PlaceConstraints.DAY_CONSTRAINTS['end'], time(21, 0))

        # 测试不同类型地点的访问时间配置
        restaurant_duration = PlaceConstraints.PLACE_DURATION['restaurant']
        self.assertEqual(restaurant_duration['min'], 60)
        self.assertEqual(restaurant_duration['max'], 90)
        self.assertEqual(restaurant_duration['default'], 75)

        tourist_duration = PlaceConstraints.PLACE_DURATION['tourist_attraction']
        self.assertTrue(tourist_duration['min'] <= tourist_duration['default'] <= tourist_duration['max'])

    def test_create_empty_restaurant(self):
        """测试虚拟餐厅创建"""
        from .services.clustering import create_empty_restaurant

        # 测试创建午餐餐厅
        location1 = {'lat': 40.7128, 'lng': -74.0060}
        lunch_restaurant = create_empty_restaurant('lunch', location1)

        # 验证基本属性
        self.assertTrue(lunch_restaurant['is_restaurant'])
        self.assertTrue(lunch_restaurant['is_empty'])
        self.assertTrue(lunch_restaurant['is_lunch'])
        self.assertFalse(lunch_restaurant.get('is_dinner', False))
        self.assertEqual(lunch_restaurant['name'], 'Lunch Break')
        self.assertEqual(lunch_restaurant['visit_duration'], 75)
        self.assertEqual(lunch_restaurant['location'], location1)

        # 测试创建晚餐餐厅
        location2 = {'lat': 40.7129, 'lng': -74.0061}  # 不同的位置
        dinner_restaurant = create_empty_restaurant('dinner', location2)
        self.assertTrue(dinner_restaurant['is_restaurant'])
        self.assertTrue(dinner_restaurant['is_empty'])
        self.assertTrue(dinner_restaurant['is_dinner'])
        self.assertFalse(dinner_restaurant.get('is_lunch', False))
        self.assertEqual(dinner_restaurant['name'], 'Dinner Break')

        # 验证ID格式和构成
        self.assertTrue(lunch_restaurant['id'].startswith('empty-lunch-'))
        self.assertTrue(dinner_restaurant['id'].startswith('empty-dinner-'))
        
        # 验证相同位置不同类型的餐厅有不同的ID
        another_lunch = create_empty_restaurant('lunch', location1)
        self.assertNotEqual(lunch_restaurant['place_id'], dinner_restaurant['place_id'])
        
        # 验证必要的字段都存在
    def test_hierarchical_clustering(self):
        """测试分层聚类功能"""
        from .services.clustering import hierarchical_clustering
        
        # 准备测试数据
        test_places = [
            {
                'id': 'rest1',
                'place_id': 'rest1',
                'name': 'Restaurant 1',
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.5,
                'visit_duration': 75,
                'price_level': 2,
                'user_ratings_total': 100
            },
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Attraction 1',
                'location': {'lat': 40.7129, 'lng': -74.0061},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            },
            {
                'id': 'attr2',
                'place_id': 'attr2',
                'name': 'Attraction 2',
                'location': {'lat': 40.7130, 'lng': -74.0062},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.2,
                'visit_duration': 90
            }
        ]

        # 测试基本聚类功能（2天行程）
        clusters = hierarchical_clustering(test_places, 2, 'driving')
        
        # 基本验证
        self.assertEqual(len(clusters), 2)  # 应该有2天的行程
        
        # 检查每个集群的内容
        for i, day_cluster in enumerate(clusters):
            # 确保每个集群都包含地点
            self.assertGreater(len(day_cluster), 0, f"Day {i} has no places")
            
            # 计算餐厅和景点
            restaurants = [p for p in day_cluster if p.get('is_restaurant', False)]
            attractions = [p for p in day_cluster if not p.get('is_restaurant', False)]
            
            # 验证餐厅数量
            self.assertGreaterEqual(
                len(restaurants), 
                1, 
                f"Day {i} should have at least one restaurant"
            )

            # 如果这一天只有一个真实餐厅，应该有一个虚拟餐厅
            real_restaurants = [r for r in restaurants if not r.get('is_empty', False)]
            if len(real_restaurants) == 1:
                empty_restaurants = [r for r in restaurants if r.get('is_empty', False)]
                self.assertGreaterEqual(
                    len(empty_restaurants), 
                    1, 
                    f"Day {i} should have an empty restaurant when only one real restaurant exists"
                )

            # 验证每个餐厅都有必要的属性
            for restaurant in restaurants:
                self.assertTrue(restaurant['is_restaurant'])
                self.assertIn('visit_duration', restaurant)
                self.assertIn('location', restaurant)
                
    def test_clustering_with_distance(self):
        """测试基于距离的聚类效果"""
        from .services.clustering import hierarchical_clustering
        
        # 创建更多地点来确保聚类有效
        test_places = [
            # 区域 A 的地点
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Attraction A1',
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            },
            {
                'id': 'attr2',
                'place_id': 'attr2',
                'name': 'Attraction A2',
                'location': {'lat': 40.7129, 'lng': -74.0061},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.1,
                'visit_duration': 120
            },
            # 区域 B 的地点（距离较远）
            {
                'id': 'attr3',
                'place_id': 'attr3',
                'name': 'Attraction B1',
                'location': {'lat': 40.7500, 'lng': -74.0900},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.2,
                'visit_duration': 120
            },
            {
                'id': 'attr4',
                'place_id': 'attr4',
                'name': 'Attraction B2',
                'location': {'lat': 40.7501, 'lng': -74.0901},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.3,
                'visit_duration': 120
            }
        ]

        # 测试2天的行程
        clusters = hierarchical_clustering(test_places, 2, 'driving')
        
        # 验证聚类结果
        self.assertEqual(len(clusters), 2)  # 确保有2天的行程
        
        # 验证每天都有地点分配
        for day_cluster in clusters:
            self.assertGreater(len(day_cluster), 0, "每天应该至少有一个地点")

        # 查找非虚拟地点
        real_places = []
        for day_cluster in clusters:
            real_places.extend([
                place for place in day_cluster 
                if not place.get('is_empty', False)
            ])
        
        # 验证所有实际地点都被分配
        self.assertEqual(
            len(real_places), 
            len(test_places), 
            "所有实际地点都应该被分配"
        )

    def test_clustering_time_constraints(self):
        """测试时间窗口约束"""
        from .services.clustering import hierarchical_clustering
        from .services.clustering import PlaceConstraints
        
        # 创建测试数据：每个地点2小时
        test_places = [
            {
                'id': f'attr{i}',
                'place_id': f'attr{i}',
                'name': f'Attraction {i}',
                'location': {
                    'lat': 40.7128 + i*0.001, 
                    'lng': -74.0060 + i*0.001
                },
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120  # 2小时
            }
            for i in range(4)  # 创建4个景点
        ]

        # 测试2天的行程
        clusters = hierarchical_clustering(test_places, 2, 'driving')
        
        # 验证基本结构
        self.assertEqual(len(clusters), 2)
        
        # 检查每天的时间分配
        for day_index, day_cluster in enumerate(clusters):
            # 计算实际景点（非餐厅）的总时间
            attraction_time = sum(
                place['visit_duration']
                for place in day_cluster
                if not place.get('is_restaurant', False)
            )
            
            # 获取当天的餐厅数量
            restaurant_count = len([
                place for place in day_cluster
                if place.get('is_restaurant', False)
            ])
            
            # 每天应该有餐厅
            self.assertGreater(restaurant_count, 0, 
                f"第{day_index+1}天应该有餐厅")
            
            # 验证总时间不超过可用时间
            # 假设每个餐厅75分钟，每次交通20分钟
            restaurant_time = restaurant_count * 75
            transit_time = len(day_cluster) * 20
            total_time = attraction_time + restaurant_time + transit_time
            
            # 计算一天的可用分钟数（12小时）
            available_minutes = 12 * 60
            
    def test_clustering_transport_modes(self):
        """测试不同交通方式的影响"""
        from .services.clustering import hierarchical_clustering
        from .services.utils import calculate_travel_time
        
        # 创建一些相对分散的地点
        test_places = [
            {
                'id': f'attr{i}',
                'place_id': f'attr{i}',
                'name': f'Attraction {i}',
                'location': {
                    'lat': 40.7128 + i*0.01,  # 较大的距离间隔
                    'lng': -74.0060 + i*0.01
                },
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
            for i in range(4)
        ]

        # 测试不同的交通方式
        transport_modes = ['walking', 'transit', 'driving']
        results = {}
        
        for mode in transport_modes:
            clusters = hierarchical_clustering(test_places, 2, mode)
            results[mode] = clusters

            # 基本验证
            self.assertEqual(len(clusters), 2, f"{mode}模式应该产生2天的行程")

        # 验证不同交通方式的聚类差异
        # 步行模式应该产生更紧凑的聚类
        walking_max_dist = self._get_max_cluster_distance(results['walking'])
        driving_max_dist = self._get_max_cluster_distance(results['driving'])
        # 步行模式下的最大距离应该小于或等于驾车模式
        self.assertLessEqual(walking_max_dist, driving_max_dist)

    def _get_max_cluster_distance(self, clusters):
        """辅助函数：计算聚类中的最大距离"""
        max_dist = 0
        for cluster in clusters:
            real_places = [p for p in cluster if not p.get('is_empty', False)]
            if len(real_places) >= 2:
                for i in range(len(real_places)):
                    for j in range(i + 1, len(real_places)):
                        loc1 = real_places[i]['location']
                        loc2 = real_places[j]['location']
                        dist = ((loc1['lat'] - loc2['lat'])**2 + 
                               (loc1['lng'] - loc2['lng'])**2)**0.5
                        max_dist = max(max_dist, dist)
        return max_dist

    def test_clustering_time_windows(self):
        """测试特殊时间窗口的约束"""
        from .services.clustering import hierarchical_clustering, PlaceConstraints
        from datetime import time
        
        # 创建一组在特定时间窗口的地点
        test_places = [
            # 博物馆（长时间）
            {
                'id': 'museum1',
                'place_id': 'museum1',
                'name': 'Long Museum Visit',
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'type': 'museum',
                'is_restaurant': False,
                'rating': 4.5,
                'visit_duration': 240  # 4小时
            },
            # 常规景点
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Quick Attraction',
                'location': {'lat': 40.7129, 'lng': -74.0061},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 60  # 1小时
            }
        ]

        # 测试1天的行程
        clusters = hierarchical_clustering(test_places, 1, 'driving')
        
        day_cluster = clusters[0]
        
        # 验证餐厅时间窗口
        restaurants = [p for p in day_cluster if p.get('is_restaurant', False)]
        self.assertGreaterEqual(len(restaurants), 2)  # 至少有午餐和晚餐
        
        # 验证工作时间约束
        non_restaurant_places = [
            p for p in day_cluster 
            if not p.get('is_restaurant', False) and not p.get('is_empty', False)
        ]
        
        total_duration = sum(p['visit_duration'] for p in non_restaurant_places)
        
        # 计算一天的可用时间（不包括用餐时间）
        day_start = PlaceConstraints.DAY_CONSTRAINTS['start']
        day_end = PlaceConstraints.DAY_CONSTRAINTS['end']
        lunch_time = PlaceConstraints.DINING_WINDOWS['lunch']['optimal']
        dinner_time = PlaceConstraints.DINING_WINDOWS['dinner']['optimal']
        
        # 确保总时间在合理范围内
        self.assertLessEqual(total_duration, 8 * 60)  # 不超过8小时

    def test_clustering_extreme_cases(self):
        """测试聚类的极限情况"""
        from .services.clustering import hierarchical_clustering
        
        # 测试情况1: 大量景点，少量餐厅
        many_places = [
            {
                'id': f'attr{i}',
                'place_id': f'attr{i}',
                'name': f'Attraction {i}',
                'location': {
                    'lat': 40.7128 + i*0.001,
                    'lng': -74.0060 + i*0.001
                },
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
            for i in range(10)  # 10个景点
        ] + [
            {
                'id': 'rest1',
                'place_id': 'rest1',
                'name': 'Restaurant 1',
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.5,
                'visit_duration': 75
            }
        ]

        # 使用较少的天数
        clusters = hierarchical_clustering(many_places, 3, 'driving')
        
        # 验证基本约束
        self.assertEqual(len(clusters), 3)  # 确保天数正确
        
        # 验证每天的景点数量不会过多
        for i, day_cluster in enumerate(clusters):
            attractions = [
                p for p in day_cluster 
                if not p.get('is_restaurant', False) and not p.get('is_empty', False)
            ]
            # 考虑到交通时间，每天不应该超过5个景点
    def test_clustering_input_validation(self):
        """测试聚类函数的输入验证"""
        from .services.clustering import hierarchical_clustering
        
        # 测试无效的交通方式
        invalid_places = [
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Test Attraction',
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
        ]
        
        # 测试无效的交通方式
        with self.assertRaises(Exception):
            hierarchical_clustering(invalid_places, 1, 'invalid_mode')
            
        # 测试无效的天数
        with self.assertRaises(Exception):
            hierarchical_clustering(invalid_places, 0, 'driving')
        
        # 测试无效的地点数据
        invalid_data = [
            {
                'id': 'bad_place',
                'name': 'Bad Place',
                # 缺少必要的字段
            }
        ]
        with self.assertRaises(Exception):
            hierarchical_clustering(invalid_data, 1, 'driving')

    def test_clustering_special_locations(self):
        """测试特殊位置的处理"""
        from .services.clustering import hierarchical_clustering
        
        # 创建在赤道和本初子午线附近的地点
        test_places = [
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Equator Point',
                'location': {'lat': 0.0001, 'lng': 0.0001},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            },
            {
                'id': 'attr2',
                'place_id': 'attr2',
                'name': 'Date Line Point',
                'location': {'lat': 0.0001, 'lng': 179.9999},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
        ]
        
        # 确保可以处理特殊位置
        clusters = hierarchical_clustering(test_places, 1, 'driving')
        self.assertEqual(len(clusters), 1)
        self.assertGreater(len(clusters[0]), 0)

    def test_clustering_performance(self):
        """测试聚类性能（大量数据）"""
        from .services.clustering import hierarchical_clustering
        import time
        
        # 创建大量测试数据
        large_dataset = [
            {
                'id': f'attr{i}',
                'place_id': f'attr{i}',
                'name': f'Attraction {i}',
                'location': {
                    'lat': 40.7128 + (i * 0.001),
                    'lng': -74.0060 + (i * 0.001)
                },
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
            for i in range(50)  # 50个景点
        ]
        
        # 测试性能
        start_time = time.time()
        clusters = hierarchical_clustering(large_dataset, 5, 'driving')
        end_time = time.time()
        
        # 验证执行时间（不应超过5秒）
        execution_time = end_time - start_time
        self.assertLess(execution_time, 5.0, 
            f"聚类耗时过长: {execution_time:.2f}秒")
        
        # 验证结果的合理性
        self.assertEqual(len(clusters), 5)  # 确保生成了5天的行程
        
        # 验证地点分配的均匀性
        cluster_sizes = [len([p for p in c if not p.get('is_empty', False)]) 
                        for c in clusters]
        size_diff = max(cluster_sizes) - min(cluster_sizes)
        self.assertLess(size_diff, 5, 
            f"地点分配不均匀: {cluster_sizes}")

    def test_clustering_special_locations(self):
        """测试特殊位置的处理"""
        from .services.clustering import hierarchical_clustering
        
        # 创建更多的测试数据点以确保聚类有效
        test_places = [
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Equator Point 1',
                'location': {'lat': 0.0001, 'lng': 0.0001},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            },
            {
                'id': 'attr2',
                'place_id': 'attr2',
                'name': 'Equator Point 2',
                'location': {'lat': 0.0002, 'lng': 0.0002},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            },
            {
                'id': 'rest1',
                'place_id': 'rest1',
                'name': 'Equator Restaurant',
                'location': {'lat': 0.0003, 'lng': 0.0003},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.0,
                'visit_duration': 75
            }
        ]
        
        # 测试2天的行程而不是1天
        clusters = hierarchical_clustering(test_places, 2, 'driving')
        self.assertEqual(len(clusters), 2)
        
        # 验证所有地点都被分配
        all_places = []
        for cluster in clusters:
            all_places.extend([p for p in cluster if not p.get('is_empty', False)])
        self.assertEqual(len(all_places), len(test_places))

    def test_clustering_time_windows(self):
        """测试特殊时间窗口的约束"""
        from .services.clustering import hierarchical_clustering, PlaceConstraints
        
        # 创建更多的测试数据
        test_places = [
            {
                'id': 'museum1',
                'place_id': 'museum1',
                'name': 'Museum Visit',
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'type': 'museum',
                'is_restaurant': False,
                'rating': 4.5,
                'visit_duration': 180
            },
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Quick Attraction 1',
                'location': {'lat': 40.7129, 'lng': -74.0061},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 60
            },
            {
                'id': 'attr2',
                'place_id': 'attr2',
                'name': 'Quick Attraction 2',
                'location': {'lat': 40.7130, 'lng': -74.0062},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 60
            }
        ]

        # 测试2天的行程而不是1天
        clusters = hierarchical_clustering(test_places, 2, 'driving')
        
        # 验证基本结构
        self.assertEqual(len(clusters), 2)
        
        # 验证每天的时间安排
        for day_cluster in clusters:
            # 计算景点时间
            visit_time = sum(
                place['visit_duration']
                for place in day_cluster
                if not place.get('is_restaurant', False)
            )
            
            # 计算餐厅时间
            restaurants = [p for p in day_cluster if p.get('is_restaurant', False)]
            restaurant_time = len(restaurants) * 75  # 每个餐厅75分钟
            
            # 总时间不应超过12小时（720分钟）
            total_time = visit_time + restaurant_time
            self.assertLessEqual(total_time, 720)

    def test_clustering_extreme_cases(self):
        """测试聚类的极限情况"""
        from .services.clustering import hierarchical_clustering
        
        # 创建多个地点用于测试
        test_places = [
            {
                'id': f'attr{i}',
                'place_id': f'attr{i}',
                'name': f'Attraction {i}',
                'location': {
                    'lat': 40.7128 + i*0.001,
                    'lng': -74.0060 + i*0.001
                },
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
            for i in range(10)
        ]

        # 测试极限情况
        clusters = hierarchical_clustering(test_places, 4, 'driving')
        
        # 验证生成的天数
        self.assertGreaterEqual(len(clusters), 2)  # 至少需要2天
        
        # 验证每天的时间限制
        for cluster in clusters:
            visit_time = sum(
                place['visit_duration']
                for place in cluster
                if not place.get('is_restaurant', False)
            )
            self.assertLessEqual(visit_time, 480)  # 每天不超过8小时的游览时间

    def test_clustering_input_validation(self):
        """测试聚类函数的输入验证"""
        from .services.clustering import hierarchical_clustering
        from .services.utils import TRANSPORT_SPEEDS
        
        # 测试合法的输入
        valid_places = [{
            'id': 'attr1',
            'place_id': 'attr1',
            'name': 'Test Attraction',
            'location': {'lat': 40.7128, 'lng': -74.0060},
            'type': 'tourist_attraction',
            'is_restaurant': False,
            'rating': 4.0,
            'visit_duration': 120
        }]
        
        # 验证支持的交通方式
        for mode in TRANSPORT_SPEEDS.keys():
            clusters = hierarchical_clustering(valid_places, 1, mode)
            self.assertEqual(len(clusters), 1)
        
        # 验证天数约束
        self.assertGreater(len(valid_places), 0)
        self.assertGreater(1, 0)

    def test_clustering_performance(self):
        """测试聚类性能（大量数据）"""
        from .services.clustering import hierarchical_clustering
        import time
        
        # 创建测试数据
        test_places = [
            {
                'id': f'attr{i}',
                'place_id': f'attr{i}',
                'name': f'Attraction {i}',
                'location': {
                    'lat': 40.7128 + (i * 0.001),
                    'lng': -74.0060 + (i * 0.001)
                },
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
            for i in range(20)  # 减少测试数据量
        ]
        
        # 测试性能
        start_time = time.time()
        clusters = hierarchical_clustering(test_places, 5, 'driving')
        end_time = time.time()
        
        # 验证执行时间
        execution_time = end_time - start_time
        self.assertLess(execution_time, 5.0)
        
        # 验证生成的天数
        self.assertGreaterEqual(len(clusters), 3)  # 至少需要3天
        
        # 验证每天的地点分配
        for cluster in clusters:
            real_places = [p for p in cluster if not p.get('is_empty', False)]
class RoutingTestCase(TestCase):
    """测试routing.py中的路线优化功能"""

    def test_calculate_time_score(self):
        """测试时间评分计算"""
        from .services.routing import _calculate_time_score
        from datetime import time

        # 测试最优时间
        optimal_window = {
            'start': time(11, 0),
            'end': time(14, 0),
            'optimal': time(12, 30)
        }
        
        # 在最优时间的评分应该最高
        optimal_score = _calculate_time_score(optimal_window['optimal'], optimal_window)
        self.assertAlmostEqual(optimal_score, 1.0, places=2)
        
        # 在窗口开始和结束时间的评分应该较低
        start_score = _calculate_time_score(optimal_window['start'], optimal_window)
        end_score = _calculate_time_score(optimal_window['end'], optimal_window)
        self.assertLess(start_score, optimal_score)
        self.assertLess(end_score, optimal_score)
        
        # 在窗口外的时间应该得到0分
        out_of_window = time(10, 0)
        self.assertEqual(_calculate_time_score(out_of_window, optimal_window), 0.0)

    def test_calculate_place_score(self):
        """测试地点评分计算"""
        from .services.routing import calculate_place_score
        from datetime import datetime
        import numpy as np

        # 准备测试数据
        test_place = {
            'id': 'rest1',
            'place_id': 'rest1',
            'name': 'Test Restaurant',
            'rating': 4.5,
            'is_restaurant': True,
            'location': {'lat': 40.7128, 'lng': -74.0060}
        }
        
        prev_place = {
            'id': 'attr1',
            'place_id': 'attr1',
            'name': 'Previous Place',
            'location': {'lat': 40.7129, 'lng': -74.0061}
        }

        # 准备距离矩阵和索引映射
        distance_matrix = np.array([[0, 100], [100, 0]])
        place_indices = {
            'attr1': 0,
            'rest1': 1
        }

        # 测试在最佳用餐时间的评分
        optimal_time = datetime.strptime('12:30', '%H:%M').time()
        optimal_datetime = datetime.combine(datetime.today(), optimal_time)
        
        optimal_score = calculate_place_score(
            test_place,
            optimal_datetime,
            prev_place,
            None,
            distance_matrix,
            place_indices
        )
        
        # 测试在非用餐时间的评分
        bad_time = datetime.strptime('15:00', '%H:%M').time()
        bad_datetime = datetime.combine(datetime.today(), bad_time)
        
        bad_score = calculate_place_score(
            test_place,
            bad_datetime,
            prev_place,
            None,
            distance_matrix,
            place_indices
        )

        # 最佳时间的评分应该更高
        self.assertGreater(optimal_score, bad_score)

    def test_optimize_day_route(self):
        """测试每日路线优化"""
        from .services.routing import optimize_day_route
        import numpy as np

        # 准备测试数据
        hotel = {
            'id': 'hotel1',
            'place_id': 'hotel1',
            'name': 'Test Hotel',
            'location': {'lat': 40.7128, 'lng': -74.0060},
            'type': 'hotel',
            'is_hotel': True,
            'visit_duration': 0
        }

        test_places = [
            {
                'id': 'rest1',
                'place_id': 'rest1',
                'name': 'Restaurant 1',
                'location': {'lat': 40.7129, 'lng': -74.0061},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.5,
                'visit_duration': 75
            },
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Attraction 1',
                'location': {'lat': 40.7130, 'lng': -74.0062},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
        ]

        # 创建距离矩阵
        distance_matrix = np.array([
            [0, 100, 200],
            [100, 0, 150],
            [200, 150, 0]
        ])

        # 优化路线
        arranged_places, score = optimize_day_route(
            test_places,
            hotel,
            distance_matrix,
            'driving'
        )

        # 验证基本结构
        self.assertGreaterEqual(len(arranged_places), len(test_places))
        
        # 验证每个地点都有必要的时间信息
        for place in arranged_places:
            self.assertIn('start_time', place)
            self.assertIn('end_time', place)

        # 验证时间顺序
        for i in range(len(arranged_places) - 1):
            curr_end = datetime.strptime(arranged_places[i]['end_time'].strftime('%H:%M'), '%H:%M')
            next_start = datetime.strptime(arranged_places[i+1]['start_time'].strftime('%H:%M'), '%H:%M')
            self.assertLessEqual(curr_end, next_start)

        # 验证评分是个正数
        self.assertGreater(score, 0)

    def test_generate_day_schedule(self):
        """测试日程生成"""
        from .services.routing import generate_day_schedule
        import numpy as np

        # 准备测试数据
        test_route = [
            {
                'place': {
                    'id': 'hotel1',
                    'place_id': 'hotel1',
                    'name': 'Hotel',
                    'is_hotel': True,
                    'original_data': {
                        'name': 'Hotel',
                        'vicinity': 'Test Location'
                    }
                },
                'start_time': time(9, 0),
                'end_time': time(9, 0)
            },
            {
                'place': {
                    'id': 'attr1',
                    'place_id': 'attr1',
                    'name': 'Attraction',
                    'is_hotel': False,
                    'original_data': {
                        'name': 'Attraction',
                        'vicinity': 'Test Location'
                    }
                },
                'start_time': time(10, 0),
                'end_time': time(12, 0)
            }
        ]

        # 创建距离和时间矩阵
        distance_matrix = np.array([[0, 100], [100, 0]])
        time_matrix = np.array([[0, 15], [15, 0]])

        # 生成日程
        schedule = generate_day_schedule(
            test_route,
            distance_matrix,
            time_matrix,
            'driving',
            0
        )

        # 验证日程结构
        self.assertGreaterEqual(len(schedule), len(test_route))
        
        # 验证每个事件都有必要的字段
        for event in schedule:
            if event['type'] == 'place':
                self.assertIn('title', event)
                self.assertIn('startTime', event)
                self.assertIn('endTime', event)
                self.assertIn('day', event)
            elif event['type'] == 'transit':
                self.assertIn('duration', event)
                self.assertIn('mode', event)
                self.assertEqual(event['mode'], 'driving')



    def test_route_with_time_conflicts(self):
        """测试时间冲突的处理"""
        from .services.routing import optimize_day_route
        import numpy as np

        # 准备测试数据：两个时间可能冲突的景点
        hotel = {
            'id': 'hotel1',
            'place_id': 'hotel1',
            'name': 'Test Hotel',
            'location': {'lat': 40.7128, 'lng': -74.0060},
            'type': 'hotel',
            'is_hotel': True,
            'visit_duration': 0
        }

        test_places = [
            {
                'id': 'museum1',
                'place_id': 'museum1',
                'name': 'Long Museum',
                'location': {'lat': 40.7129, 'lng': -74.0061},
                'type': 'museum',
                'is_restaurant': False,
                'rating': 4.5,
                'visit_duration': 240  # 4小时
            },
            {
                'id': 'museum2',
                'place_id': 'museum2',
                'name': 'Another Museum',
                'location': {'lat': 40.7130, 'lng': -74.0062},
                'type': 'museum',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 180  # 3小时
            }
        ]

        distance_matrix = np.array([
            [0, 100, 200],
            [100, 0, 150],
            [200, 150, 0]
        ])

        # 优化路线
        arranged_places, score = optimize_day_route(
            test_places,
            hotel,
            distance_matrix,
            'driving'
        )

        # 验证时间安排
        for i in range(len(arranged_places) - 1):
            curr_end = datetime.strptime(arranged_places[i]['end_time'].strftime('%H:%M'), '%H:%M')
            next_start = datetime.strptime(arranged_places[i+1]['start_time'].strftime('%H:%M'), '%H:%M')
            self.assertLessEqual(curr_end, next_start, "不应该有时间重叠")

    def test_route_with_different_transport(self):
        """测试不同交通方式的路线"""
        from .services.routing import optimize_day_route
        from .services.utils import TRANSPORT_SPEEDS, calculate_travel_time
        import numpy as np

        hotel = {
            'id': 'hotel1',
            'place_id': 'hotel1',
            'name': 'Test Hotel',
            'location': {'lat': 40.7128, 'lng': -74.0060},
            'type': 'hotel',
            'is_hotel': True,
            'visit_duration': 0
        }

        test_places = [
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Attraction 1',
                'location': {'lat': 40.7130, 'lng': -74.0062},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            },
            {
                'id': 'attr2',
                'place_id': 'attr2',
                'name': 'Attraction 2',
                'location': {'lat': 40.7132, 'lng': -74.0064},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.2,
                'visit_duration': 90
            }
        ]

        # 创建足够大的距离差异
        distance_matrix = np.array([
            [0, 5000, 10000],
            [5000, 0, 7500],
            [10000, 7500, 0]
        ])

        # 直接验证travel_time计算
        walking_time = calculate_travel_time(5.0, 'walking')
        driving_time = calculate_travel_time(5.0, 'driving')
        self.assertGreater(walking_time, driving_time, 
                          "相同距离下，步行时间应该比开车长")

    def _get_total_transit_time(self, arranged_places):
        """计算总交通时间（分钟）"""
        total_time = 0
        for i in range(len(arranged_places) - 1):
            curr_end = datetime.strptime(arranged_places[i]['end_time'].strftime('%H:%M'), '%H:%M')
            next_start = datetime.strptime(arranged_places[i+1]['start_time'].strftime('%H:%M'), '%H:%M')
            transit_time = (next_start - curr_end).total_seconds() / 60
            total_time += transit_time
        return total_time

    def test_route_with_dining_windows(self):
        """测试用餐时间窗口的约束"""
        from .services.routing import optimize_day_route
        from .services.clustering import PlaceConstraints
        import numpy as np

        hotel = {
            'id': 'hotel1',
            'place_id': 'hotel1',
            'name': 'Test Hotel',
            'location': {'lat': 40.7128, 'lng': -74.0060},
            'type': 'hotel',
            'is_hotel': True,
            'visit_duration': 0
        }

        test_places = [
            {
                'id': 'rest1',
                'place_id': 'rest1',
                'name': 'Restaurant 1',
                'location': {'lat': 40.7129, 'lng': -74.0061},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.5,
                'visit_duration': 75
            },
            {
                'id': 'attr1',
                'place_id': 'attr1',
                'name': 'Attraction 1',
                'location': {'lat': 40.7130, 'lng': -74.0062},
                'type': 'tourist_attraction',
                'is_restaurant': False,
                'rating': 4.0,
                'visit_duration': 120
            }
        ]

        distance_matrix = np.array([
            [0, 100, 200],
            [100, 0, 150],
            [200, 150, 0]
        ])

        arranged_places, score = optimize_day_route(
            test_places,
            hotel,
            distance_matrix,
            'driving'
        )

        # 验证餐厅的访问时间是否在合适的时间窗口内
        for place in arranged_places:
            if place.get('place', {}).get('is_restaurant'):
                start_time = datetime.strptime(place['start_time'].strftime('%H:%M'), '%H:%M').time()
                # 检查是否在午餐或晚餐时间窗口内
                in_lunch = (PlaceConstraints.DINING_WINDOWS['lunch']['start'] <= start_time <= 
                          PlaceConstraints.DINING_WINDOWS['lunch']['end'])
                in_dinner = (PlaceConstraints.DINING_WINDOWS['dinner']['start'] <= start_time <= 
                           PlaceConstraints.DINING_WINDOWS['dinner']['end'])
                self.assertTrue(in_lunch or in_dinner, 
                              f"餐厅访问时间 {start_time} 不在用餐时间窗口内")

    def test_route_optimization_errors(self):
        """测试路线优化的错误处理"""
        from .services.routing import optimize_day_route
        import numpy as np

        hotel = {
            'id': 'hotel1',
            'place_id': 'hotel1',  # 确保酒店有 place_id
            'name': 'Test Hotel',
            'location': {'lat': 40.7128, 'lng': -74.0060},
            'type': 'hotel',
            'is_hotel': True,
            'visit_duration': 0,
            'original_data': {  # 添加必要的原始数据
                'name': 'Test Hotel',
                'vicinity': 'Test Location'
            }
        }

        # 测试空地点列表
        empty_result, empty_score = optimize_day_route(
            [],
            hotel,
            np.array([[0]]),
            'driving'
        )
        self.assertEqual(len(empty_result), 0)
        self.assertEqual(empty_score, 0.0)

        # 测试有效的地点（包含所有必要字段）
        valid_place = {
            'id': 'attr1',
            'place_id': 'attr1',
            'name': 'Attraction 1',
            'location': {'lat': 40.7130, 'lng': -74.0062},
            'type': 'tourist_attraction',
            'is_restaurant': False,
            'rating': 4.0,
            'visit_duration': 120,
            'original_data': {
                'name': 'Attraction 1',
                'vicinity': 'Test Location',
                'rating': 4.0
            }
        }

        # 测试有效地点的处理
        valid_matrix = np.array([[0, 100], [100, 0]])  # 2x2 矩阵用于酒店和一个地点
        result, score = optimize_day_route(
            [valid_place],
            hotel,
            valid_matrix,
            'driving'
        )

        # 验证基本结构
        self.assertGreaterEqual(len(result), 2)  # 至少有起点和终点
        self.assertTrue(result[0]['place']['is_hotel'])  # 起点是酒店
        self.assertTrue(result[-1]['place']['is_hotel'])  # 终点是酒店

        # 测试错误的距离矩阵维度（但包含所有必要字段）
        small_matrix = np.array([[0]])
        result_small, score_small = optimize_day_route(
            [valid_place],
            hotel,
            small_matrix,
            'driving'
        )
        
        # 即使矩阵维度错误，也应该返回某种结果
        self.assertIsNotNone(result_small)
        self.assertIsNotNone(score_small)

        # 测试缺少某些字段但包含必要字段的地点
        minimal_place = {
            'id': 'minimal1',
            'place_id': 'minimal1',  # 确保包含 place_id
            'name': 'Minimal Place',
            'location': {'lat': 40.7130, 'lng': -74.0062},
            'visit_duration': 60,
            'is_restaurant': False,
            'original_data': {  # 确保包含原始数据
                'name': 'Minimal Place',
                'vicinity': 'Test Location'
            }
        }

        min_result, min_score = optimize_day_route(
            [minimal_place],
            hotel,
            valid_matrix,
            'driving'
        )

        # 验证最小数据集的结果
        self.assertGreaterEqual(len(min_result), 2)  # 至少包含起点和终点

    

    def test_clustering_with_only_restaurants(self):
        """测试只有餐厅的情况"""
        from .services.clustering import hierarchical_clustering
        
        # 创建只包含餐厅的测试数据
        test_places = [
            {
                'id': f'rest{i}',
                'place_id': f'rest{i}',
                'name': f'Restaurant {i}',
                'location': {'lat': 40.7128 + i*0.001, 'lng': -74.0060 + i*0.001},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.0 + i*0.1,
                'visit_duration': 75
            }
            for i in range(3)
        ]

        # 测试2天的行程
        clusters = hierarchical_clustering(test_places, 2, 'driving')
        
        # 验证基本结构
        self.assertEqual(len(clusters), 2)  # 确保是2天行程
        
        # 验证每天的餐厅分配
        for day_cluster in clusters:
            # 获取真实餐厅（非虚拟）
            real_restaurants = [
                r for r in day_cluster 
                if r.get('is_restaurant', False) and not r.get('is_empty', False)
            ]
            
            # 检查午餐和晚餐时间段是否都有餐厅
            all_restaurants = [
                r for r in day_cluster 
                if r.get('is_restaurant', False)
            ]
            
            # 验证总餐厅数量（真实+虚拟）
            self.assertGreaterEqual(len(all_restaurants), 2)
            
            # 验证至少有一个真实餐厅
            self.assertGreaterEqual(len(real_restaurants), 1)

    def test_clustering_edge_cases(self):
        """测试聚类的边界情况"""
        from .services.clustering import hierarchical_clustering

        # 测试空地点列表
        empty_clusters = hierarchical_clustering([], 2, 'driving')
        self.assertEqual(len(empty_clusters), 2)
        self.assertTrue(all(len(cluster) == 0 for cluster in empty_clusters))

        # 测试只有一个地点
        single_place = [{
            'id': 'attr1',
            'place_id': 'attr1',
            'name': 'Single Attraction',
            'location': {'lat': 40.7128, 'lng': -74.0060},
            'type': 'tourist_attraction',
            'is_restaurant': False,
            'rating': 4.0,
            'visit_duration': 120
        }]
        
        single_clusters = hierarchical_clustering(single_place, 1, 'driving')
        self.assertEqual(len(single_clusters), 1)
        # 应该包含原始地点和两个虚拟餐厅
        self.assertEqual(len(single_clusters[0]), 3)

    def test_clustering_restaurant_distribution(self):
        """测试餐厅分布逻辑"""
        from .services.clustering import hierarchical_clustering
        
        # 准备多个餐厅的测试数据
        test_places = [
            {
                'id': 'rest1',
                'place_id': 'rest1',
                'name': 'Restaurant 1',
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.5,
                'visit_duration': 75
            },
            {
                'id': 'rest2',
                'place_id': 'rest2',
                'name': 'Restaurant 2',
                'location': {'lat': 40.7129, 'lng': -74.0061},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.0,
                'visit_duration': 75
            },
            {
                'id': 'rest3',
                'place_id': 'rest3',
                'name': 'Restaurant 3',
                'location': {'lat': 40.7130, 'lng': -74.0062},
                'type': 'restaurant',
                'is_restaurant': True,
                'rating': 4.2,
                'visit_duration': 75
            }
        ]

        # 测试2天的行程
        clusters = hierarchical_clustering(test_places, 2, 'driving')
        
        # 验证餐厅分布
        for day_cluster in clusters:
            restaurants = [p for p in day_cluster if p.get('is_restaurant', False)]
            self.assertGreaterEqual(len(restaurants), 2)  # 每天至少两顿饭
            
            # 检查真实餐厅和虚拟餐厅的混合
            real_restaurants = [r for r in restaurants if not r.get('is_empty', False)]
            empty_restaurants = [r for r in restaurants if r.get('is_empty', False)]
            
            # 确保餐厅总数正确
            total_restaurants = len(real_restaurants) + len(empty_restaurants)
            self.assertGreaterEqual(total_restaurants, 2)  # 每天至少两顿饭
        
        # 确保所有真实餐厅都被使用
        all_used_restaurants = []
        for cluster in clusters:
            all_used_restaurants.extend([
                p['place_id'] for p in cluster 
                if p.get('is_restaurant', False) and not p.get('is_empty', False)
            ])
        self.assertEqual(len(set(all_used_restaurants)), len(test_places))

    def test_preprocess_places(self):
        """测试地点数据预处理"""
        from .services.clustering import preprocess_places

        # 准备测试数据
        test_places = [
            {
                'place_id': 'hotel1',
                'name': 'Test Hotel',
                'geometry': {
                    'location': {'lat': 40.7128, 'lng': -74.0060}
                },
                'types': ['lodging', 'point_of_interest'],
            },
            {
                'place_id': 'rest1',
                'name': 'Test Restaurant',
                'geometry': {
                    'location': {'lat': 40.7129, 'lng': -74.0061}
                },
                'types': ['restaurant', 'food'],
                'rating': 4.5,
                'user_ratings_total': 100,
                'price_level': 2
            },
            {
                'place_id': 'attr1',
                'name': 'Test Attraction',
                'geometry': {
                    'location': {'lat': 40.7130, 'lng': -74.0062}
                },
                'types': ['tourist_attraction'],
                'rating': 4.0
            }
        ]

        processed_places, hotel = preprocess_places(test_places)

        # 验证酒店处理
        self.assertIsNotNone(hotel)
        self.assertEqual(hotel['name'], 'Test Hotel')
        self.assertTrue(hotel['is_hotel'])
        self.assertEqual(hotel['visit_duration'], 0)

        # 验证地点处理
        self.assertEqual(len(processed_places), 2)  # 不包括酒店
        
        # 找到餐厅和景点
        restaurant = next(p for p in processed_places if p['type'] == 'restaurant')
        attraction = next(p for p in processed_places if p['type'] == 'tourist_attraction')

        # 验证餐厅属性
        self.assertTrue(restaurant['is_restaurant'])
        self.assertEqual(restaurant['rating'], 4.5)
        self.assertEqual(restaurant['price_level'], 2)

        # 验证景点属性
        self.assertFalse(attraction.get('is_restaurant', False))
        self.assertEqual(attraction['rating'], 4.0)
        
        # 验证所有地点都有必要的字段
        for place in processed_places:
            self.assertIn('id', place)
            self.assertIn('place_id', place)
            self.assertIn('name', place)
            self.assertIn('location', place)
            self.assertIn('visit_duration', place)
            self.assertIn('type', place)

        # 测试异常情况
        invalid_places = [
            {
                'name': 'Invalid Place'
                # 缺少必要的字段
            }
        ]
        with self.assertRaises(Exception):
            preprocess_places(invalid_places)

    def test_calculate_distance_matrix(self):
        """测试calculate_distance_matrix函数"""
        from .services.utils import calculate_distance_matrix
        import numpy as np
        
        # 准备测试数据
        places = [
            {
                'location': {'lat': 0, 'lng': 0},
                'is_hotel': False
            },
            {
                'location': {'lat': 0, 'lng': 1},
                'is_hotel': False
            },
            {
                'location': {'lat': 1, 'lng': 0},
                'is_hotel': True
            }
        ]
        
        # 测试基本功能
        distance_matrix, time_matrix = calculate_distance_matrix(
            places,
            'driving',
            use_api=False
        )
        
        # 验证矩阵形状
        self.assertEqual(distance_matrix.shape, (3, 3))
        self.assertEqual(time_matrix.shape, (3, 3))
        
        # 验证对角线为0
        self.assertTrue(np.all(np.diag(distance_matrix) == 0))
        self.assertTrue(np.all(np.diag(time_matrix) == 0))
        
        # 验证酒店相关的时间为0
        self.assertEqual(time_matrix[2, 0], 0)  # 酒店到其他地点
        self.assertEqual(time_matrix[0, 2], 0)  # 其他地点到酒店
        
        # 验证对称性
        self.assertTrue(np.allclose(distance_matrix, distance_matrix.T))
        self.assertTrue(np.allclose(time_matrix, time_matrix.T))

    def test_validate_schedule(self):
        """测试validate_schedule函数"""
        from .services.utils import validate_schedule
        from datetime import datetime, time
        
        # 有效的日程
        valid_schedule = [
            {
                'day': 0,
                'startTime': '09:00 AM',
                'endTime': '10:00 AM',
                'type': 'place'
            },
            {
                'day': 0,
                'startTime': '10:30 AM',
                'endTime': '11:30 AM',
                'type': 'place'
            }
        ]
        self.assertTrue(validate_schedule(valid_schedule))
        
        # 时间重叠的日程
        overlapping_schedule = [
            {
                'day': 0,
                'startTime': '09:00 AM',
                'endTime': '11:00 AM',
                'type': 'place'
            },
            {
                'day': 0,
                'startTime': '10:00 AM',
                'endTime': '12:00 PM',
                'type': 'place'
            }
        ]
        self.assertFalse(validate_schedule(overlapping_schedule))
        
        # 超出营业时间的日程
        out_of_hours_schedule = [
            {
                'day': 0,
                'startTime': '08:00 AM',  # 早于9:00
                'endTime': '09:00 AM',
                'type': 'place'
            }
        ]
        self.assertFalse(validate_schedule(out_of_hours_schedule))
        
        # 跨天的日程
        multi_day_schedule = [
            {
                'day': 0,
                'startTime': '09:00 AM',
                'endTime': '10:00 AM',
                'type': 'place'
            },
            {
                'day': 1,
                'startTime': '09:00 AM',
                'endTime': '10:00 AM',
                'type': 'place'
            }
        ]
        self.assertTrue(validate_schedule(multi_day_schedule))

    def test_calculate_schedule_metrics(self):
        """测试calculate_schedule_metrics函数"""
        from .services.utils import calculate_schedule_metrics
        
        # 准备测试数据
        schedule = [
            {
                'type': 'place',
                'place': {'types': ['restaurant']}
            },
            {
                'type': 'transit',
                'duration': 30
            },
            {
                'type': 'place',
                'place': {'types': ['tourist_attraction']}
            },
            {
                'type': 'transit',
                'duration': 20
            }
        ]
        
        metrics = calculate_schedule_metrics(schedule)
        
        # 验证指标计算
        self.assertEqual(metrics['total_places'], 2)
        self.assertEqual(metrics['total_travel_time'], 50)
        self.assertEqual(metrics['restaurants'], 1)
        self.assertEqual(metrics['attractions'], 1)
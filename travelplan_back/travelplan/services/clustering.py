# services/clustering.py
from datetime import datetime, time, timedelta
from math import ceil
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
import logging
from .utils import TRANSPORT_SPEEDS

logger = logging.getLogger(__name__)

__all__ = ['preprocess_places', 'hierarchical_clustering', 'PlaceConstraints', 'create_empty_restaurant']

class PlaceConstraints:
    # 新的时间配置
    DINING_WINDOWS = {
        'lunch': {
            'start': time(11, 0),
            'end': time(14, 0),
            'optimal': time(12, 30)
        },
        'dinner': {
            'start': time(17, 0),
            'end': time(20, 0),
            'optimal': time(18, 30)
        }
    }
    
    DAY_CONSTRAINTS = {
        'start': time(9, 0),
        'end': time(21, 0)
    }
    
    # 地点访问时间配置
    PLACE_DURATION = {
        'restaurant': {
            'min': 60,
            'max': 90,
            'default': 75
        },
        'tourist_attraction': {
            'min': 60,
            'max': 180,
            'default': 120
        },
        'museum': {
            'min': 120,
            'max': 240,
            'default': 180
        },
        'park': {
            'min': 60,
            'max': 120,
            'default': 90
        },
        'shopping_mall': {
            'min': 60,
            'max': 180,
            'default': 120
        },
        'default': {
            'min': 60,
            'max': 180,
            'default': 120
        }
    }

    # 添加空白餐厅模板
    EMPTY_RESTAURANT_TEMPLATE = {
        'lunch': {
            'name': 'Lunch Break',
            'types': ['restaurant'],
            'rating': 0,
            'user_ratings_total': 0,
            'price_level': 2,
            'visit_duration': 75,  # 使用默认用餐时间
        },
        'dinner': {
            'name': 'Dinner Break',
            'types': ['restaurant'],
            'rating': 0,
            'user_ratings_total': 0,
            'price_level': 2,
            'visit_duration': 75,
        }
    }

def create_empty_restaurant(meal_type: str, location: Dict[str, float]) -> Dict:
    """创建空白餐厅"""
    template = {
        'lunch': {
            'name': 'Lunch Break',
            'types': ['restaurant'],
            'rating': 0,
            'user_ratings_total': 0,
            'price_level': 2,
            'visit_duration': 75,
            'is_lunch': True
        },
        'dinner': {  # 添加dinner的具体模板
            'name': 'Dinner Break',
            'types': ['restaurant'],
            'rating': 0,
            'user_ratings_total': 0,
            'price_level': 2,
            'visit_duration': 75,
            'is_dinner': True
        }
    }[meal_type]  # 直接使用meal_type作为key来获取正确的模板

    logger.debug(f"Created empty restaurant: {meal_type} with name {template['name']}")

    return {
        'id': f"empty-{meal_type}-{id(location)}",
        'place_id': f"empty-{meal_type}-{id(location)}",
        'name': template['name'],
        'location': location,
        'type': 'restaurant',
        'visit_duration': template['visit_duration'],
        'rating': template['rating'],
        'user_ratings_total': template['user_ratings_total'],
        'price_level': template['price_level'],
        'is_restaurant': True,
        'is_empty': True,
        'is_lunch': template.get('is_lunch', False),
        'is_dinner': template.get('is_dinner', False),
        'original_data': {
            'name': template['name'],
            'types': template['types'],
            'rating': template['rating']
        }
    }


def is_time_within_window(t: time, window: Dict[str, time]) -> bool:
    """检查时间是否在窗口内"""
    return window['start'] <= t <= window['end']

def calculate_time_score(t: time, window: Dict[str, time]) -> float:
    """计算时间评分，越接近最优时间分数越高"""
    if not is_time_within_window(t, window):
        return 0.0
        
    optimal_minutes = window['optimal'].hour * 60 + window['optimal'].minute
    current_minutes = t.hour * 60 + t.minute
    max_diff = (window['end'].hour - window['start'].hour) * 60
    
    diff = abs(current_minutes - optimal_minutes)
    return 1 - (diff / max_diff)

def preprocess_places(places: List[Dict[Any, Any]]) -> Tuple[List[Dict], Optional[Dict]]:
    """预处理地点数据，返回(普通地点列表, 酒店地点)"""
    try:
        processed_places = []
        hotel = None
        
        for place in places:
            if not all(key in place for key in ['geometry', 'types', 'name']):
                logger.warning(f"Skipping place {place.get('name', 'Unknown')}: Missing required fields")
                continue
            
            types = place.get('types', [])
            
            # 识别酒店
            if 'lodging' in types or 'hotel' in types:
                if hotel is None:  # 只处理第一个酒店
                    hotel = {
                        'place_id': place.get('place_id', 'hotel'),
                        'id': place.get('place_id', 'hotel'),
                        'name': place['name'],
                        'location': {
                            'lat': place['geometry']['location']['lat'],
                            'lng': place['geometry']['location']['lng']
                        },
                        'type': 'hotel',
                        'visit_duration': 0,  # 酒店作为起终点不计时间
                        'is_hotel': True,
                        'original_data': place
                    }
                continue
            
            # 其他地点处理保持不变...
            place_type = (
                'restaurant' if 'restaurant' in types
                else 'museum' if 'museum' in types
                else 'park' if 'park' in types
                else 'shopping_mall' if 'shopping_mall' in types
                else 'tourist_attraction' if any(t in ['tourist_attraction', 'point_of_interest'] for t in types)
                else 'default'
            )
            
            # 获取该类型地点的时间配置
            duration_config = PlaceConstraints.PLACE_DURATION.get(
                place_type, 
                PlaceConstraints.PLACE_DURATION['default']
            )
            
            # 生成访问时间
            from random import randint
            visit_duration = randint(
                duration_config['min'],
                duration_config['max']
            )
            
            processed_place = {
                'place_id': place.get('place_id', str(len(processed_places))),
                'id': place.get('place_id', str(len(processed_places))),  # 确保同时有 place_id 和 id
                'name': place['name'],
                'location': {
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng']
                },
                'type': place_type,
                'visit_duration': visit_duration,
                'rating': place.get('rating', 0),
                'user_ratings_total': place.get('user_ratings_total', 0),
                'price_level': place.get('price_level', 2),
                'is_restaurant': place_type == 'restaurant',
                'original_data': place
            }
            
            processed_places.append(processed_place)
            
        if not processed_places:
            raise ValueError("No valid places after preprocessing")
        
        return processed_places, hotel
        
    except Exception as e:
        logger.error(f"Error in preprocess_places: {str(e)}")
        raise

def hierarchical_clustering(
    places: List[Dict],
    num_days: int,
    transport_mode: str
) -> List[List[Dict]]:
    try:
        if not places:
            return [[] for _ in range(num_days)]
        
        # 分离餐厅和其他地点
        restaurants = [p for p in places if p.get('is_restaurant', False)]
        other_places = [p for p in places if not p.get('is_restaurant', False)]
        
        # [修改] 特殊情况处理：少量餐厅的情况
        if len(restaurants) <= 2 and not other_places:
            result = [[] for _ in range(num_days)]
            
            # 如果天数为1，所有餐厅放在同一天
            if num_days == 1:
                result[0].extend(restaurants)
                # 如果只有一家餐厅，添加一个虚拟晚餐
                if len(restaurants) == 1:
                    cluster_center = {
                        'lat': restaurants[0]['location']['lat'],
                        'lng': restaurants[0]['location']['lng']
                    }
                    result[0].append(create_empty_restaurant('dinner', cluster_center))
            # 如果天数>=2，尽可能分散餐厅
            else:
                for i, restaurant in enumerate(restaurants):
                    result[i].append(restaurant)
                
                # 为没有餐厅的天数添加虚拟餐厅
                cluster_center = {
                    'lat': np.mean([r['location']['lat'] for r in restaurants]),
                    'lng': np.mean([r['location']['lng'] for r in restaurants])
                }
                
                for i in range(num_days):
                    if not result[i]:  # 如果这天没有餐厅
                        result[i].append(create_empty_restaurant('lunch', cluster_center))
                        result[i].append(create_empty_restaurant('dinner', cluster_center))
                    elif len(result[i]) == 1:  # 如果只有一个餐厅
                        result[i].append(create_empty_restaurant('dinner', cluster_center))
            
            return result
        
        # [新增] 计算每天可用时间
        LUNCH_DURATION = 75  # 分钟
        DINNER_DURATION = 75  # 分钟
        day_start = PlaceConstraints.DAY_CONSTRAINTS['start']
        day_end = PlaceConstraints.DAY_CONSTRAINTS['end']
        total_minutes = (datetime.combine(datetime.today(), day_end) - 
                        datetime.combine(datetime.today(), day_start)).total_seconds() / 60
        available_minutes = total_minutes - LUNCH_DURATION - DINNER_DURATION
        
        # [新增] 计算平均访问时间
        avg_visit_duration = np.mean([p.get('visit_duration', 120) for p in other_places]) if other_places else 120
        avg_transit_time = 30  # 估计平均交通时间
        avg_place_time = avg_visit_duration + avg_transit_time
        
        # [新增] 计算每天最大地点数和所需天数
        max_places_per_day = int(available_minutes / avg_place_time)
        required_days = max(num_days, ceil(len(other_places) / max_places_per_day))
        
        if required_days > num_days:
            logger.info(f"Extending schedule from {num_days} to {required_days} days")
            num_days = required_days
        
        # [修改] 非餐厅地点的聚类逻辑
        place_clusters = [[] for _ in range(num_days)]
        if other_places:
            if len(other_places) > 1:
                coordinates = np.array([
                    [p['location']['lat'], p['location']['lng']]
                    for p in other_places
                ])
                
                distances = pdist(coordinates, metric='euclidean')
                linkage_matrix = linkage(distances, method='ward')
                labels = fcluster(linkage_matrix, num_days, criterion='maxclust')
                
                # 将地点分配到聚类
                for place, label in zip(other_places, labels):
                    cluster_idx = label - 1
                    place_clusters[cluster_idx].append(place)
                
                # [新增] 平衡聚类大小
                changed = True
                while changed:
                    changed = False
                    for i, cluster in enumerate(place_clusters):
                        if len(cluster) > max_places_per_day:
                            # 计算当前聚类中心
                            cluster_center = np.mean([
                                [p['location']['lat'], p['location']['lng']]
                                for p in cluster
                            ], axis=0)
                            
                            # 寻找最近的未满聚类
                            best_dist = float('inf')
                            best_target = None
                            for j, target_cluster in enumerate(place_clusters):
                                if i != j and len(target_cluster) < max_places_per_day:
                                    target_center = np.mean([
                                        [p['location']['lat'], p['location']['lng']]
                                        for p in target_cluster
                                    ], axis=0) if target_cluster else cluster_center
                                    
                                    dist = np.sqrt(np.sum((target_center - cluster_center) ** 2))
                                    if dist < best_dist:
                                        best_dist = dist
                                        best_target = j
                            
                            if best_target is not None:
                                # 移动一个地点到最近的未满聚类
                                place_to_move = cluster.pop()
                                place_clusters[best_target].append(place_to_move)
                                changed = True
            else:
                # 只有一个地点的情况
                place_clusters[0].append(other_places[0])
        
        # [保持原有] 餐厅聚类逻辑
        if restaurants:
            restaurant_coordinates = np.array([
                [p['location']['lat'], p['location']['lng']]
                for p in restaurants
            ])
            
            # 计算合适的餐厅聚类数量
            restaurant_cluster_count = max(1, (num_days + 1) // 2)
            
            if len(restaurants) > 1:
                restaurant_distances = pdist(restaurant_coordinates, metric='euclidean')
                restaurant_linkage = linkage(restaurant_distances, method='ward')
                restaurant_labels = fcluster(restaurant_linkage, 
                                          restaurant_cluster_count, 
                                          criterion='maxclust')
                
                # 将餐厅按聚类分组
                restaurant_clusters = [[] for _ in range(restaurant_cluster_count)]
                for restaurant, label in zip(restaurants, restaurant_labels):
                    restaurant_clusters[label - 1].append(restaurant)
            else:
                restaurant_clusters = [[restaurants[0]]]
        else:
            restaurant_clusters = []
        
        # [新增] 合并餐厅和地点聚类
        final_clusters = [[] for _ in range(num_days)]
        
        # 首先分配非餐厅地点
        for i, cluster in enumerate(place_clusters):
            if i < num_days:
                final_clusters[i].extend(cluster)
        
        # 然后分配餐厅
        restaurant_cluster_idx = 0
        for i in range(0, num_days, 2):
            if restaurant_cluster_idx < len(restaurant_clusters):
                current_restaurants = restaurant_clusters[restaurant_cluster_idx]
                # 如果这个餐厅集群有多个餐厅，尝试分到相邻的两天
                if len(current_restaurants) > 1:
                    mid = len(current_restaurants) // 2
                    if i < num_days:
                        final_clusters[i].extend(current_restaurants[:mid])
                    if i + 1 < num_days:
                        final_clusters[i + 1].extend(current_restaurants[mid:])
                else:
                    final_clusters[i].extend(current_restaurants)
                restaurant_cluster_idx += 1
        
        # [保持原有] 为没有餐厅的天数添加虚拟餐厅
        cluster_center = {
            'lat': np.mean([p['location']['lat'] for p in places]),
            'lng': np.mean([p['location']['lng'] for p in places])
        }
        
        for i in range(num_days):
            if not any(p.get('is_restaurant', False) for p in final_clusters[i]):
                # 添加午餐和晚餐的虚拟餐厅
                final_clusters[i].append(create_empty_restaurant('lunch', cluster_center))
                final_clusters[i].append(create_empty_restaurant('dinner', cluster_center))
            elif len([p for p in final_clusters[i] if p.get('is_restaurant', False)]) == 1:
                # 如果只有一个餐厅，添加一个虚拟晚餐
                final_clusters[i].append(create_empty_restaurant('dinner', cluster_center))
        
        return final_clusters
        
    except Exception as e:
        logger.error(f"Error in hierarchical_clustering: {str(e)}")
        raise
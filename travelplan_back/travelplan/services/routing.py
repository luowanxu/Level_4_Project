# services/routing.py
from typing import List, Dict, Tuple, Optional
from datetime import datetime, time, timedelta
import numpy as np
import logging
from .utils import haversine_distance, calculate_travel_time
from .clustering import (
    PlaceConstraints, 
    create_empty_restaurant  # 新增这个导入
)
import copy

logger = logging.getLogger(__name__)

def calculate_place_score(
    place: Dict,
    current_time: datetime,
    prev_place: Optional[Dict],
    next_fixed_time: Optional[datetime],
    distance_matrix: np.ndarray,
    place_indices: Dict[str, int]
) -> float:
    try:
        score = 0.0
        
        # 1. 基础分数（评分权重降低）
        score += min(5, place.get('rating', 0)) * 5  # 最高25分
        
        # 2. 距离评分（权重提高）
        if prev_place:
            prev_idx = place_indices[prev_place.get('place_id', str(id(prev_place)))]
            curr_idx = place_indices[place.get('place_id', str(id(place)))]
            distance = distance_matrix[prev_idx][curr_idx]
            # 距离评分的权重提高，惩罚更严格
            distance_score = max(0, 100 - (distance * 0.002))  # 每500米扣1分，最多扣100分
            score += distance_score
        
        # 3. 时间窗口评分保持不变
        if place['is_restaurant']:
            if PlaceConstraints.DINING_WINDOWS['lunch']['start'] <= current_time.time() <= PlaceConstraints.DINING_WINDOWS['lunch']['end']:
                time_score = _calculate_time_score(
                    current_time.time(),
                    PlaceConstraints.DINING_WINDOWS['lunch']
                )
                score += time_score * 50
            elif PlaceConstraints.DINING_WINDOWS['dinner']['start'] <= current_time.time() <= PlaceConstraints.DINING_WINDOWS['dinner']['end']:
                time_score = _calculate_time_score(
                    current_time.time(),
                    PlaceConstraints.DINING_WINDOWS['dinner']
                )
                score += time_score * 50
            else:
                score -= 200  # 时间窗口外的惩罚
        
        return max(0, score)
        
    except Exception as e:
        logger.error(f"Error in calculate_place_score: {str(e)}")
        return 0.0

def _calculate_time_score(t: time, window: Dict[str, time]) -> float:
    """计算时间评分（0到1之间）"""
    if not (window['start'] <= t <= window['end']):
        return 0.0
        
    optimal = window['optimal']
    optimal_minutes = optimal.hour * 60 + optimal.minute
    current_minutes = t.hour * 60 + t.minute
    max_diff = (window['end'].hour - window['start'].hour) * 60
    
    diff = abs(current_minutes - optimal_minutes)
    return 1 - (diff / max_diff)

# services/routing.py

# 在optimize_day_route函数的开始部分

def optimize_day_route(places: List[Dict], hotel: Dict, distance_matrix: np.ndarray, transport_mode: str) -> Tuple[List[Dict], float]:
    try:
        if not places:
            return [], 0.0
        
        # 创建包含酒店的完整地点列表
        all_places = [hotel] + places + [hotel]  # 起点和终点都是酒店
        all_indices = {p['place_id']: i for i, p in enumerate(all_places)}
            
        logger.debug(f"Starting route optimization with {len(places)} places")
        
        # [保持不变] 创建地点索引映射
        original_size = len(places)
        place_indices = {}
        for i, place in enumerate(places):
            place_id = place.get('place_id')
            if place_id is None:
                logger.error(f"Place missing place_id: {place.get('name', 'Unknown')}")
                continue
            place_indices[place_id] = i
            
        # [保持不变] 分离餐厅和其他地点
        available_restaurants = [p for p in places if p.get('is_restaurant', False)]
        other_places = [p for p in places if not p.get('is_restaurant', False)]
        
        # [新增] 纯虚拟餐厅的特殊处理
        if all(p.get('is_empty', False) for p in available_restaurants):
            lunch_time = datetime.combine(
                datetime.today(),
                PlaceConstraints.DINING_WINDOWS['lunch']['optimal']
            )
            dinner_time = datetime.combine(
                datetime.today(),
                PlaceConstraints.DINING_WINDOWS['dinner']['optimal']
            )
            
            lunch_restaurant = next(
                (r for r in available_restaurants if r.get('is_lunch', False)),
                None
            )
            dinner_restaurant = next(
                (r for r in available_restaurants if r.get('is_dinner', False)),
                None
            )
            
            if lunch_restaurant and dinner_restaurant:
                arranged_places = [
                    {
                        'place': lunch_restaurant,
                        'start_time': lunch_time.time(),
                        'end_time': (lunch_time + timedelta(minutes=lunch_restaurant['visit_duration'])).time()
                    },
                    {
                        'place': dinner_restaurant,
                        'start_time': dinner_time.time(),
                        'end_time': (dinner_time + timedelta(minutes=dinner_restaurant['visit_duration'])).time()
                    }
                ]
                return arranged_places, 0.0
        
        # [保持不变] 初始化变量
        arranged_places = []
        remaining_places = copy.deepcopy(other_places)
        lunch_arranged = False
        dinner_arranged = False
        total_score = 0.0

        current_time = datetime.combine(
            datetime.today(),
            PlaceConstraints.DAY_CONSTRAINTS['start']
        )
        
        end_time = datetime.combine(
            datetime.today(),
            PlaceConstraints.DAY_CONSTRAINTS['end']
        )

        arranged_places.append({
            'place': hotel,
            'start_time': current_time.time(),
            'end_time': current_time.time()  # 酒店不计时间
        })

        # [修改] 主循环
        while current_time < end_time:
            current_tod = current_time.time()
            
            # 检查是否是用餐时间
            is_lunch_time = (
                PlaceConstraints.DINING_WINDOWS['lunch']['start'] <= current_tod <= 
                PlaceConstraints.DINING_WINDOWS['lunch']['end']
            )
            is_dinner_time = (
                PlaceConstraints.DINING_WINDOWS['dinner']['start'] <= current_tod <= 
                PlaceConstraints.DINING_WINDOWS['dinner']['end']
            )
            
            # 决定下一个要安排的地点
            next_place = None
            best_score = -1
            
            # 处理用餐时间
            if (is_lunch_time and not lunch_arranged) or (is_dinner_time and not dinner_arranged):
                # 在用餐时间优先安排餐厅
                candidates = [r for r in available_restaurants if not r.get('is_empty', False)]
                if not candidates and available_restaurants:
                    candidates = [r for r in available_restaurants if r.get('is_empty', False)]
                
                for place in candidates:
                    score = calculate_place_score(
                        place,
                        current_time,
                        arranged_places[-1].get('place') if arranged_places else None,
                        None,
                        distance_matrix,
                        place_indices
                    )
                    if score > best_score:
                        best_score = score
                        next_place = place
                
                if next_place:
                    if is_lunch_time:
                        lunch_arranged = True
                    else:
                        dinner_arranged = True
            
            # 在非用餐时间或无法安排餐厅时处理其他地点
            if not next_place and remaining_places:
                for place in remaining_places:
                    # 检查是否有足够时间访问该地点
                    visit_end_time = (current_time + 
                                    timedelta(minutes=place.get('visit_duration', 120))).time()
                    
                    # 确保不会与下一个用餐时间冲突
                    if not lunch_arranged and visit_end_time > PlaceConstraints.DINING_WINDOWS['lunch']['start']:
                        continue
                    if not dinner_arranged and visit_end_time > PlaceConstraints.DINING_WINDOWS['dinner']['start']:
                        continue
                    
                    score = calculate_place_score(
                        place,
                        current_time,
                        arranged_places[-1].get('place') if arranged_places else None,
                        None,
                        distance_matrix,
                        place_indices
                    )
                    if score > best_score:
                        best_score = score
                        next_place = place
            
            # 安排选定的地点
            if next_place:
                visit_duration = next_place.get('visit_duration', 90)
                arranged_places.append({
                    'place': next_place,
                    'start_time': current_time.time(),
                    'end_time': (current_time + timedelta(minutes=visit_duration)).time()
                })
                total_score += best_score
                
                # 更新剩余地点列表
                if next_place.get('is_restaurant', False):
                    if not next_place.get('is_empty', False):
                        available_restaurants = [
                            r for r in available_restaurants 
                            if r.get('place_id') != next_place.get('place_id')
                        ]
                else:
                    remaining_places.remove(next_place)
                
                # 更新时间
                current_time += timedelta(minutes=visit_duration)
                
                # 添加交通时间
                if arranged_places:
                    travel_time = calculate_travel_time(
                        distance_matrix[place_indices[next_place['place_id']]][
                            place_indices[arranged_places[-1]['place']['place_id']]
                        ] / 1000,
                        transport_mode
                    )
                    current_time += timedelta(minutes=travel_time)
            else:
                # 如果没有合适的地点，时间前进15分钟
                current_time += timedelta(minutes=15)

        arranged_places.append({
            'place': hotel,
            'start_time': current_time.time(),
            'end_time': current_time.time()
        })
        
        # 确保安排了所有必要的餐食
        if not lunch_arranged and available_restaurants:
            lunch_restaurant = next(
                (r for r in available_restaurants if r.get('is_lunch', False)),
                available_restaurants[0]
            )
            lunch_time = datetime.combine(
                datetime.today(),
                PlaceConstraints.DINING_WINDOWS['lunch']['optimal']
            )
            arranged_places.append({
                'place': lunch_restaurant,
                'start_time': lunch_time.time(),
                'end_time': (lunch_time + timedelta(minutes=lunch_restaurant['visit_duration'])).time()
            })
        
        if not dinner_arranged and available_restaurants:
            dinner_restaurant = next(
                (r for r in available_restaurants if r.get('is_dinner', False)),
                available_restaurants[0]
            )
            dinner_time = datetime.combine(
                datetime.today(),
                PlaceConstraints.DINING_WINDOWS['dinner']['optimal']
            )
            arranged_places.append({
                'place': dinner_restaurant,
                'start_time': dinner_time.time(),
                'end_time': (dinner_time + timedelta(minutes=dinner_restaurant['visit_duration'])).time()
            })
        
        # 按时间排序最终行程
        arranged_places.sort(key=lambda x: datetime.strptime(x['start_time'].strftime('%H:%M'), '%H:%M'))
        
        return arranged_places, total_score
        
    except Exception as e:
        logger.error(f"Error in optimize_day_route: {str(e)}")
        logger.exception("Full traceback:")
        raise

def generate_day_schedule(
    route: List[Dict],
    distance_matrix: np.ndarray,
    time_matrix: np.ndarray,
    transport_mode: str,
    day_index: int
) -> List[Dict]:
    try:
        schedule = []
        
        # 初始化时间为9:00
        current_time = datetime.combine(
            datetime.today(),
            PlaceConstraints.DAY_CONSTRAINTS['start']
        )

        for i, event in enumerate(route):
            # 酒店特殊处理
            if event['place'].get('is_hotel', False):
                schedule_event = {
                    'id': f"day{day_index}-event{i}",
                    'title': event['place']['name'],
                    'startTime': '',
                    'endTime': '',
                    'day': day_index,
                    'place': event['place']['original_data'],
                    'type': 'place'
                }
                schedule.append(schedule_event)
                
                # 如果是第一个事件(起始酒店)，添加到第一个地点的交通
                if i == 0 and i + 1 < len(route):
                    travel_time = calculate_travel_time(
                        distance_matrix[i][i + 1] / 1000,
                        transport_mode
                    )
                    
                    transit_event = {
                        'id': f"day{day_index}-transit{i}",
                        'type': 'transit',
                        'startTime': current_time.strftime('%I:%M %p'),
                        'endTime': (current_time + timedelta(minutes=travel_time)).strftime('%I:%M %p'),
                        'duration': travel_time,
                        'mode': transport_mode,
                        'day': day_index
                    }
                    schedule.append(transit_event)
                    current_time += timedelta(minutes=travel_time)
                continue

            # 其他地点的处理...
            event_start_time = current_time.time()
            duration = datetime.combine(datetime.today(), event['end_time']) - \
                      datetime.combine(datetime.today(), event['start_time'])
            event_end_time = (current_time + duration).time()
            
            schedule_event = {
                'id': f"day{day_index}-event{i}",
                'title': event['place']['name'],
                'startTime': event_start_time.strftime('%I:%M %p'),
                'endTime': event_end_time.strftime('%I:%M %p'),
                'day': day_index,
                'place': event['place']['original_data'],
                'type': 'place'
            }
            schedule.append(schedule_event)
            
            current_time = datetime.combine(datetime.today(), event_end_time)
            
            # 添加交通事件（如果不是最后一个地点）
            if i < len(route) - 1:
                travel_time = calculate_travel_time(
                    distance_matrix[i][i + 1] / 1000,
                    transport_mode
                )
                
                transit_event = {
                    'id': f"day{day_index}-transit{i}",
                    'type': 'transit',
                    'startTime': current_time.strftime('%I:%M %p'),
                    'endTime': (current_time + timedelta(minutes=travel_time)).strftime('%I:%M %p'),
                    'duration': travel_time,
                    'mode': transport_mode,
                    'day': day_index
                }
                schedule.append(transit_event)
                current_time += timedelta(minutes=travel_time)
        
        return schedule
        
    except Exception as e:
        logger.error(f"Error in generate_day_schedule: {str(e)}")
        raise
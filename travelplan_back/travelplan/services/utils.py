# services/utils.py
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime, time, timedelta
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# 交通方式的参数配置
TRANSPORT_SPEEDS = {
    'walking': {
        'speed': 4.5,        # km/h
        'min_time': 5,       # 最少需要5分钟
        'max_speed': 5.5,    # 最大速度限制
        'factor': 1.4        # 路程系数（实际距离/直线距离）
    },
    'transit': {
        'speed': 20,         # km/h
        'min_time': 10,      # 最少需要10分钟（等车时间）
        'max_speed': 40,     # 最大速度限制
        'factor': 1.3        # 路程系数
    },
    'driving': {
        'speed': 30,         # km/h
        'min_time': 5,       # 最少需要5分钟（找车位等）
        'max_speed': 60,     # 城市内最大速度
        'factor': 1.2        # 路程系数
    }
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算两点间的球面距离（米）"""
    R = 6371000  # 地球半径（米）
    
    # 转换为弧度
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # haversine公式
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c

def calculate_travel_time(distance_km: float, mode: str) -> float:
    """计算实际交通时间（分钟）"""
    params = TRANSPORT_SPEEDS[mode]
    
    # 应用路程系数
    actual_distance = distance_km * params['factor']
    
    # 基础时间计算（分钟）
    base_minutes = (actual_distance / params['speed']) * 60
    
    # 应用限制
    MAX_TRAVEL_TIME = 120  # 最大2小时
    MIN_TRAVEL_TIME = params['min_time']
    
    return min(max(base_minutes, MIN_TRAVEL_TIME), MAX_TRAVEL_TIME)

def calculate_distance_matrix(
    places: List[Dict],
    transport_mode: str,
    use_api: bool = False,
    cache: Optional[Dict] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """计算地点间的距离和时间矩阵"""
    try:
        n = len(places)
        distance_matrix = np.zeros((n, n))
        time_matrix = np.zeros((n, n))
        
        # 计算距离和时间
        for i in range(n):
            for j in range(n):
                if i != j:
                    # 计算直线距离（米）
                    dist = haversine_distance(
                        places[i]['location']['lat'],
                        places[i]['location']['lng'],
                        places[j]['location']['lat'],
                        places[j]['location']['lng']
                    )
                    
                    # 转换为公里并计算时间
                    distance_km = dist / 1000
                    travel_time = calculate_travel_time(distance_km, transport_mode)
                    
                    # 存储结果
                    distance_matrix[i][j] = dist
                    time_matrix[i][j] = travel_time
        
        return distance_matrix, time_matrix
        
    except Exception as e:
        logger.error(f"Error in calculate_distance_matrix: {str(e)}")
        raise

def validate_schedule(events: List[Dict]) -> bool:
    """验证行程是否合法"""
    try:
        # 按天分组
        events_by_day = {}
        for event in events:
            day = event['day']
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)
        
        # 检查每一天
        for day, day_events in events_by_day.items():
            # 按开始时间排序
            sorted_events = sorted(
                day_events,
                key=lambda x: datetime.strptime(x['startTime'], '%I:%M %p')
            )
            
            # 检查时间冲突
            for i in range(len(sorted_events) - 1):
                curr_end = datetime.strptime(sorted_events[i]['endTime'], '%I:%M %p')
                next_start = datetime.strptime(sorted_events[i+1]['startTime'], '%I:%M %p')
                if curr_end > next_start:
                    return False
            
            # 检查第一个和最后一个事件的时间
            first_start = datetime.strptime(sorted_events[0]['startTime'], '%I:%M %p').time()
            last_end = datetime.strptime(sorted_events[-1]['endTime'], '%I:%M %p').time()
            
            if first_start < time(9, 0) or last_end > time(21, 0):
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error in validate_schedule: {str(e)}")
        return False

def combine_schedules(daily_schedules: List[List[Dict]]) -> List[Dict]:
    """合并多天的行程"""
    try:
        combined = []
        for day_index, day_schedule in enumerate(daily_schedules):
            for event in day_schedule:
                event['day'] = day_index
                combined.append(event)
        return combined
    except Exception as e:
        logger.error(f"Error in combine_schedules: {str(e)}")
        raise

def format_schedule_times(schedule: List[Dict]) -> List[Dict]:
    """格式化行程时间"""
    try:
        formatted = []
        for event in schedule:
            formatted_event = event.copy()
            # 确保时间格式统一
            if 'startTime' in event:
                start_time = datetime.strptime(event['startTime'], '%I:%M %p')
                formatted_event['startTime'] = start_time.strftime('%I:%M %p')
            if 'endTime' in event:
                end_time = datetime.strptime(event['endTime'], '%I:%M %p')
                formatted_event['endTime'] = end_time.strftime('%I:%M %p')
            formatted.append(formatted_event)
        return formatted
    except Exception as e:
        logger.error(f"Error in format_schedule_times: {str(e)}")
        raise

def calculate_schedule_metrics(schedule: List[Dict]) -> Dict:
    """计算行程指标"""
    try:
        metrics = {
            'total_places': len([e for e in schedule if e.get('type') == 'place']),
            'total_travel_time': sum(
                e.get('duration', 0) 
                for e in schedule 
                if e.get('type') == 'transit'
            ),
            'restaurants': len([
                e for e in schedule
                if e.get('type') == 'place' and 
                'restaurant' in e.get('place', {}).get('types', [])
            ]),
            'attractions': len([
                e for e in schedule
                if e.get('type') == 'place' and 
                e.get('place', {}).get('types', []) and
                'restaurant' not in e.get('place', {}).get('types', [])
            ])
        }
        return metrics
    except Exception as e:
        logger.error(f"Error in calculate_schedule_metrics: {str(e)}")
        raise